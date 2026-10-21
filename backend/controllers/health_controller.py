from fastapi import APIRouter

from controllers.dependencies import AnalysisServiceDependency, SettingsDependency
from llm.prompts import PROMPT_VERSION
from schemas.system import HealthResponse
from services.triage_policy import POLICY_VERSION

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
@router.get("/status", response_model=HealthResponse)
async def health(
    service: AnalysisServiceDependency, settings: SettingsDependency
) -> HealthResponse:
    """Service liveness/configuration only; this endpoint never spends model quota."""
    return HealthResponse(
        provider=service.llm.provider,
        model=service.llm.model,
        prompt_version=PROMPT_VERSION,
        policy_version=POLICY_VERSION,
        max_input_chars=settings.max_input_chars,
    )
