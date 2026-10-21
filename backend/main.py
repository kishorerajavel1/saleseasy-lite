"""Application composition root. Run with uvicorn main:create_app --factory."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from controllers import analysis_controller, health_controller, inventory_controller
from controllers.error_handlers import analysis_error, request_validation_error
from core.config import Settings
from core.logging import configure_logging
from llm.base import LLMClient
from llm.factory import create_llm
from middleware.request_limits import RequestLimits
from services.analysis_service import AnalysisError, AnalysisService

EXPOSED_HEADERS = [
    "X-Request-ID",
    "X-Analysis-Model",
    "X-Analysis-Attempts",
    "X-Analysis-Latency-Ms",
    "X-Policy-Version",
    "Retry-After",
]


def create_app(settings: Settings | None = None, llm: LLMClient | None = None) -> FastAPI:
    configure_logging()
    settings = settings or Settings()
    provider = llm if llm is not None else create_llm(settings)
    app = FastAPI(
        title="SalesEasy Lite API",
        version="0.1.0",
        description="Fictional field-sales triage. Recommendations only; no actions are executed.",
    )
    app.state.settings = settings
    app.state.analysis_service = AnalysisService(provider, settings)
    app.add_exception_handler(RequestValidationError, request_validation_error)
    app.add_exception_handler(AnalysisError, analysis_error)
    app.include_router(analysis_controller.router)
    app.include_router(health_controller.router)
    app.include_router(inventory_controller.router)
    app.add_middleware(RequestLimits, settings=settings)
    # Added last so browser origins receive CORS headers even on limit/error responses.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=EXPOSED_HEADERS,
        allow_credentials=False,
    )
    return app
