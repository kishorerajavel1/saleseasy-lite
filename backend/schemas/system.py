from typing import Literal

from schemas.analysis import StrictModel


class HealthResponse(StrictModel):
    status: Literal["ok"] = "ok"
    provider: Literal["gemini", "groq"]
    model: str
    prompt_version: str
    policy_version: str
    max_input_chars: int
    live_model_checked: bool = False


class InventoryRecord(StrictModel):
    id: str
    outlet: str
    sku: str
    system_stock: int
