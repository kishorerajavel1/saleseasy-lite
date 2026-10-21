"""Evaluate the configured LLM provider: python -m evaluation.run --repeat 3 --delay 15."""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from core.config import BACKEND_ROOT, Settings
from llm.base import TransientProviderError
from llm.factory import create_llm
from llm.prompts import PROMPT_VERSION
from schemas import Analysis
from services.analysis_service import AnalysisError, AnalysisService
from services.triage_policy import POLICY_VERSION

CASES = json.loads((Path(__file__).parent / "cases.json").read_text())


class SimulatedFailureLLM:
    """Evaluation-only boundary used to exercise the real service failure contract."""

    provider = "simulated_failure"

    def __init__(self, model: str):
        self.model = model
        self.calls = 0

    async def interpret(self, text: str, repair: str | None = None):
        self.calls += 1
        raise TransientProviderError


def assertions(case: dict, output: Analysis) -> list[str]:
    Analysis.model_validate(output.model_dump())
    errors = []
    for expected_key, field in (
        ("category", "issue_category"),
        ("action", "recommended_next_action"),
        ("urgency", "urgency"),
        ("review", "needs_human_review"),
    ):
        if getattr(output, field) != case[expected_key]:
            errors.append(f"{field}: expected {case[expected_key]}, got {getattr(output, field)}")
    if "stock" in case and not any(
        e.source == "verified_table" and f"system_stock={case['stock']} units" in e.reference
        for e in output.evidence
    ):
        errors.append("expected inventory evidence missing")
    if not any(e.source == "field_update" and e.reference in case["text"] for e in output.evidence):
        errors.append("original field claim missing")
    for expected in case.get("missing_contains", []):
        if expected.casefold() not in " ".join(output.missing_information).casefold():
            errors.append(f"missing follow-up: {expected}")
    if case.get("reason_contains", "").casefold() not in (output.review_reason or "").casefold():
        errors.append("expected review rationale missing")
    generated = " ".join(output.missing_information + [output.review_reason or ""])
    if any(word in generated.casefold() for word in ("food poisoning", "salmonella", "infection")):
        errors.append("generated diagnostic language")
    if any(c.isdigit() for c in generated):
        errors.append("unsupported generated numeric assertion")
    return errors


async def run(repeat: int, delay: float, output: Path) -> int:
    settings = Settings()
    adapter = create_llm(settings)
    service = AnalysisService(adapter, settings)
    records = []
    for iteration in range(1, repeat + 1):
        for case in CASES:
            if case.get("mode") == "simulated_failure":
                simulated = SimulatedFailureLLM(adapter.model)
                try:
                    await AnalysisService(simulated, settings).analyze(case["text"])
                    actual = {"status": 200, "error_code": None, "attempts": simulated.calls}
                except AnalysisError as error:
                    actual = {
                        "status": error.status_code,
                        "error_code": error.code,
                        "attempts": simulated.calls,
                    }
                errors = [
                    f"{field}: expected {case[field]}, got {actual[field]}"
                    for field in ("status", "error_code", "attempts")
                    if actual[field] != case[field]
                ]
                records.append(
                    {
                        "id": case["id"],
                        "iteration": iteration,
                        "mode": "simulated_failure",
                        "model": adapter.model,
                        "expected": case,
                        "actual": actual,
                        "latency_ms": None,
                        "attempts": actual["attempts"],
                        "error_code": actual["error_code"],
                        "pass": not errors,
                        "failed_assertions": errors,
                    }
                )
                print(f"{'PASS' if not errors else 'FAIL'} {case['id']} simulated")
                continue
            try:
                result = await service.analyze(case["text"])
                actual = result.analysis.model_dump()
                errors = assertions(case, result.analysis)
                latency, attempts = result.latency_ms, result.attempts
                error_code = None
            except AnalysisError as error:
                actual = None
                errors = [error.code]
                error_code = error.code
                latency, attempts = None, None
            records.append(
                {
                    "id": case["id"],
                    "iteration": iteration,
                    "mode": "live",
                    "model": adapter.model,
                    "expected": case,
                    "actual": actual,
                    "latency_ms": latency,
                    "attempts": attempts,
                    "error_code": error_code,
                    "pass": not errors,
                    "failed_assertions": errors,
                }
            )
            print(
                f"{'PASS' if not errors else 'FAIL'} {case['id']} "
                + (f"{latency}ms" if latency is not None else error_code)
            )
            if delay:
                await asyncio.sleep(delay)
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": adapter.provider,
        "model": adapter.model,
        "prompt_version": PROMPT_VERSION,
        "policy_version": POLICY_VERSION,
        "successful_live_cases": sum(r["pass"] for r in records if r["mode"] == "live"),
        "successful_simulated_cases": sum(
            r["pass"] for r in records if r["mode"] == "simulated_failure"
        ),
        "results": records,
    }
    await asyncio.to_thread(write_report, output, report, records)
    return 0 if all(r["pass"] for r in records) else 1


def write_report(output: Path, report: dict, records: list[dict]):
    output.mkdir(parents=True, exist_ok=True)
    stem = f"{report['provider']}-results"
    (output / f"{stem}.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        f"# {report['provider'].title()} evaluation",
        "",
        f"Generated: {report['generated_at']}",
        f"Model: {report['model']}",
        f"Prompt: {report['prompt_version']}",
        f"Policy: {report['policy_version']}",
        f"Passed: {sum(record['pass'] for record in records)}/{len(records)}",
        "",
        "| Case | Run | Expected category / action | Actual category / action | Result |",
        "|---|---|---|---|---|",
    ]
    for record in records:
        expected, actual = record["expected"], record["actual"]
        if record["mode"] == "simulated_failure":
            expected_summary = f"HTTP {expected['status']} / {expected['error_code']}"
            actual_summary = f"HTTP {actual['status']} / {actual['error_code']}"
        else:
            expected_summary = f"{expected['category']} / {expected['action']}"
            actual_summary = (
                f"{actual['issue_category']} / {actual['recommended_next_action']}"
                if actual
                else record["error_code"]
            )
        lines.append(
            f"| {record['id']} | {record['iteration']} | "
            f"{expected_summary} | "
            f"{actual_summary} | {'PASS' if record['pass'] else 'FAIL'} |"
        )
    lines.extend(["", "Full outputs and failed assertions are in the adjacent JSON report.", ""])
    (output / f"{stem}.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--delay", type=float, default=15, help="Seconds between live cases")
    parser.add_argument("--output", type=Path, default=BACKEND_ROOT / "evaluation" / "results")
    args = parser.parse_args()
    if args.repeat < 1 or args.delay < 0:
        parser.error("repeat must be positive and delay nonnegative")
    raise SystemExit(asyncio.run(run(args.repeat, args.delay, args.output)))


if __name__ == "__main__":
    main()
