"""Public seven-field contract and the smaller, private LLM extraction contract."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Category = Literal[
    "out_of_stock",
    "stock_discrepancy",
    "competitor_pricing",
    "product_safety",
    "commercial_request",
    "prompt_injection_attempt",
    "other",
]
Urgency = Literal["low", "medium", "high", "critical"]
Action = Literal[
    "request_restock",
    "verify_stock_physically",
    "escalate_to_quality_team",
    "route_to_pricing_manager",
    "request_more_info",
    "flag_for_security_review",
    "no_action_needed",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AnalyzeRequest(StrictModel):
    text: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def nonblank(self):
        if not self.text.strip() or not any(char.isalnum() for char in self.text):
            raise ValueError("A field update containing words or numbers is required.")
        if any(ord(char) < 32 and char not in "\t\n\r" for char in self.text):
            raise ValueError("Unsupported control characters.")
        return self


class Evidence(StrictModel):
    source: Literal["field_update", "verified_table"]
    reference: str = Field(min_length=1, max_length=2000)
    verified: bool

    @model_validator(mode="after")
    def source_controls_verification(self):
        if self.verified != (self.source == "verified_table"):
            raise ValueError("Only verified-table evidence can be marked verified.")
        return self


class Analysis(StrictModel):
    issue_category: Category
    urgency: Urgency
    evidence: list[Evidence] = Field(min_length=1, max_length=16)
    recommended_next_action: Action
    missing_information: list[str] = Field(max_length=12)
    needs_human_review: bool
    review_reason: str | None = Field(max_length=2000)

    @model_validator(mode="after")
    def review_reason_required(self):
        if self.needs_human_review:
            if not self.review_reason or not self.review_reason.strip():
                raise ValueError("Human review requires a nonempty reason.")
        elif self.review_reason is not None:
            raise ValueError("Review reason must be null when review is not required.")
        return self
