"""Translate the HTTP request/response boundary; business policy lives in services."""

import json
import logging

from fastapi import APIRouter, HTTPException, Request, Response

from controllers.dependencies import AnalysisServiceDependency, SettingsDependency
from schemas.analysis import Analysis, AnalyzeRequest
from services.triage_policy import POLICY_VERSION

router = APIRouter(tags=["Analysis"])
logger = logging.getLogger("saleseasy.analysis")


@router.post("/analyze", response_model=Analysis)
async def analyze(
    body: AnalyzeRequest,
    response: Response,
    request: Request,
    service: AnalysisServiceDependency,
    settings: SettingsDependency,
) -> Analysis:
    if len(body.text) > settings.max_input_chars:
        raise HTTPException(status_code=422, detail="Field update is too long.")
    result = await service.analyze(body.text)
    response.headers.update(
        {
            "X-Analysis-Model": result.model,
            "X-Analysis-Attempts": str(result.attempts),
            "X-Analysis-Latency-Ms": str(result.latency_ms),
            "X-Policy-Version": POLICY_VERSION,
        }
    )
    logger.info(
        json.dumps(
            {
                "event": "analysis",
                "request_id": request.state.request_id,
                "model": result.model,
                "category": result.analysis.issue_category,
                "urgency": result.analysis.urgency,
                "review": result.analysis.needs_human_review,
                "attempts": result.attempts,
                "latency_ms": result.latency_ms,
            }
        )
    )
    return result.analysis
