"""Deterministic final-response builder; commercial actions are never executed."""

from domain.signals import detect, detect_details, negated
from schemas import Analysis, Evidence, Interpretation, Observation
from services.inventory_service import Resolution, resolve

POLICY_VERSION = "2026-10-21.2"
QUESTIONS = {
    "outlet": "Which outlet is affected?",
    "sku": "Which SKU and pack size are affected?",
    "association": "Clarify the outlet and SKU association for each issue.",
    "inventory": "What is the current physical stock count and when was it checked?",
    "competitor_name": "What is the competitor name?",
    "observed_price": "What is the observed competitor price and offer period?",
    "locations": "Which specific locations have the competitor offer?",
    "proof": "Can you provide a photo, receipt, or other supporting evidence?",
    "impact": "What is the measured sales impact and its supporting evidence?",
    "batch": "What are the batch number, expiry date, and affected quantity?",
    "customer": "What was reported by the customer, and when did it happen?",
    "commercial": (
        "What commercial concession is requested and what supporting evidence is available?"
    ),
    "clarity": "What issue needs attention and what was directly observed?",
}
REASONS = {
    "safety": "Reported health or product safety concern requires urgent quality-team review.",
    "damage": "Reported product damage requires human quality-team review.",
    "pricing": (
        "Commercial or pricing decisions require an authorized human; no concession is approved."
    ),
    "conflict": (
        "The field claim conflicts with system-recorded stock; physical verification is required."
    ),
    "injection": (
        "An instruction override attempt was detected in untrusted field data and was not followed."
    ),
    "impact": "The claimed sales impact is unverified and requires human assessment.",
    "missing": (
        "Missing or ambiguous outlet/product information prevents reliable inventory matching."
    ),
    "unverified": (
        "The reported stock condition cannot be corroborated from the verified inventory."
    ),
    "clarity": "The update needs human clarification before a reliable recommendation can be made.",
}
RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def supported_observations(text: str, interpretation: Interpretation) -> list[Observation]:
    """Quotes must exist verbatim; obvious local negations cannot become positive signals."""
    result = []
    for item in interpretation.observations:
        start = text.find(item.quote)
        if start < 0 or not item.quote.strip():
            raise ValueError("unsupported_observation_quote")
        if item.kind not in ("injection", "routine") and negated(
            text, start, item.kind, item.quote
        ):
            continue
        result.append(item)
    for item in interpretation.provided_details:
        if item.quote not in text or not item.quote.strip():
            raise ValueError("unsupported_detail_quote")
    return result


def build_analysis(
    text: str,
    interpretation: Interpretation,
) -> Analysis:
    resolution: Resolution = resolve(text)
    deterministic = detect(text)
    semantic = supported_observations(text, interpretation)
    observations = deterministic + semantic
    kinds = {o.kind for o in observations}
    reasons: list[str] = []
    questions: list[str] = []
    category, action, urgency = "other", "request_more_info", "medium"

    def reason(code: str):
        if code not in reasons:
            reasons.append(code)

    def question(code: str):
        if QUESTIONS[code] not in questions:
            questions.append(QUESTIONS[code])

    if kinds & {"illness", "hazard", "damage"}:
        category, action = "product_safety", "escalate_to_quality_team"
        urgency = "critical" if kinds & {"illness", "hazard"} else "high"
        reason("safety" if urgency == "critical" else "damage")
        question("batch")
        if "illness" in kinds:
            question("customer")
    elif kinds & {"pricing", "commercial"}:
        category = "competitor_pricing" if "pricing" in kinds else "commercial_request"
        action = "route_to_pricing_manager"
    elif "stockout" in kinds or "in_stock" in kinds:
        row = resolution.row
        conflict = row and (
            ("stockout" in kinds and row.system_stock > 0)
            or ("in_stock" in kinds and row.system_stock == 0)
        )
        if conflict:
            category, action, urgency = "stock_discrepancy", "verify_stock_physically", "high"
            reason("conflict")
            question("inventory")
        elif "stockout" in kinds and row and row.system_stock == 0:
            category, action = "out_of_stock", "request_restock"
        elif "in_stock" in kinds and row and row.system_stock > 0:
            action, urgency = "no_action_needed", "low"
        else:
            category = "out_of_stock" if "stockout" in kinds else "other"
            reason("unverified")
            question("inventory")
    elif "low_stock" in kinds:
        question("inventory")
        reason("unverified")
    elif "injection" in kinds:
        category, action = "prompt_injection_attempt", "flag_for_security_review"
    elif kinds and kinds <= {"routine", "irrelevant"}:
        action, urgency = "no_action_needed", "low"
    else:
        reason("clarity")
        question("clarity")

    # Independent review flags cannot replace a higher-priority category/action.
    if kinds & {"pricing", "commercial"}:
        reason("pricing")
    if "pricing" in kinds:
        provided = {d.name for d in detect_details(text)}
        if interpretation:
            provided.update(d.name for d in interpretation.provided_details)
        if resolution.skus:
            provided.add("sku")
        for name in ("competitor_name", "sku", "observed_price", "locations", "proof"):
            if name not in provided:
                question(name)
    elif "commercial" in kinds:
        question("commercial")
    if "injection" in kinds:
        reason("injection")
        if RANK[urgency] < RANK["medium"]:
            urgency = "medium"
        if action == "no_action_needed":
            category, action = "prompt_injection_attempt", "flag_for_security_review"
    if "impact" in kinds:
        reason("impact")
        question("impact")
    # Outlet is not a prerequisite for routing pricing or a stand-alone attack.
    needs_entity = bool(
        kinds & {"illness", "hazard", "damage", "stockout", "in_stock", "low_stock", "impact"}
    ) and category not in ("competitor_pricing", "commercial_request", "prompt_injection_attempt")
    if needs_entity:
        if not resolution.outlets:
            question("outlet")
        if not resolution.skus:
            question("sku")
        if not resolution.row:
            reason("missing")
        if resolution.ambiguous or (resolution.outlets and resolution.skus and not resolution.row):
            question("association")
    evidence: list[Evidence] = []
    seen = set()
    # Preserve signal quotes, including a claim as a claim even if it agrees with inventory.
    for observation in observations:
        if observation.quote not in seen:
            evidence.append(
                Evidence(source="field_update", reference=observation.quote, verified=False)
            )
            seen.add(observation.quote)
        if len(evidence) == 12:
            break
    if not evidence:
        evidence.append(Evidence(source="field_update", reference=text, verified=False))
    if resolution.row and kinds & {
        "illness",
        "hazard",
        "damage",
        "stockout",
        "in_stock",
        "low_stock",
        "impact",
    }:
        evidence.append(
            Evidence(
                source="verified_table",
                reference=resolution.row.reference,
                verified=True,
            )
        )

    response = Analysis(
        issue_category=category,
        urgency=urgency,
        evidence=evidence,
        recommended_next_action=action,
        missing_information=questions,
        needs_human_review=bool(reasons),
        review_reason=" ".join(REASONS[r] for r in reasons) if reasons else None,
    )
    # Re-validate after all policy decisions; no unchecked model text reaches prose fields.
    return Analysis.model_validate(response.model_dump())
