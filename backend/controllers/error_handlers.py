import json
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.analysis_service import AnalysisError

logger = logging.getLogger("saleseasy.analysis")


async def analysis_error(request: Request, error: AnalysisError) -> JSONResponse:
    logger.warning(
        json.dumps(
            {
                "event": "analysis_failed",
                "request_id": request.state.request_id,
                "error_code": error.code,
                "status_code": error.status_code,
            }
        )
    )
    return JSONResponse(
        status_code=error.status_code,
        content={"code": error.code, "detail": error.message},
    )


async def request_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    """Avoid echoing raw updates and exception contexts in validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in error.errors()
            ]
        },
    )
