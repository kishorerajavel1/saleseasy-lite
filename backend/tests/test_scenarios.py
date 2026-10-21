import pytest

from evaluation.run import CASES, assertions
from schemas import Interpretation
from services.triage_policy import build_analysis

POLICY_CASES = [case for case in CASES if case.get("mode") != "simulated_failure"]


@pytest.mark.parametrize("case", POLICY_CASES, ids=lambda case: case["id"])
def test_assignment_policy_scenarios(case):
    # Tests deterministic policy only; semantic provider behavior is evaluated live.
    output = build_analysis(case["text"], Interpretation(observations=[], provided_details=[]))
    assert assertions(case, output) == []
