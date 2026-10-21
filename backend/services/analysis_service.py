"""Bounded LLM interpretation followed by grounding and deterministic policy."""

import asyncio
import time
from dataclasses import dataclass

from pydantic import ValidationError

from core.config import Settings
from llm.base import (
    BlockedModelOutput,
    InvalidModelOutput,
    LLMClient,
    ProviderRequestError,
    ProviderTimeoutError,
    TransientProviderError,
)
from schemas import Analysis, Interpretation
from services.triage_policy import build_analysis, supported_observations


class AnalysisError(Exception):
    """Safe application error; provider exception text never crosses the API boundary."""

    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class AnalysisResult:
    analysis: Analysis
    model: str
    attempts: int
    latency_ms: int


class AnalysisService:
    def __init__(self, llm: LLMClient, settings: Settings):
        self.llm = llm
        self.settings = settings
        self.slots = asyncio.Semaphore(settings.max_concurrent_analyses)

    async def analyze(self, text: str) -> AnalysisResult:
        started = time.monotonic()
        repair = None
        try:
            # The overall budget includes queueing and at most one validation repair.
            async with asyncio.timeout(self.settings.model_total_timeout_seconds):
                async with self.slots:
                    for attempt in range(1, 3):
                        try:
                            async with asyncio.timeout(self.settings.model_attempt_timeout_seconds):
                                proposal = await self.llm.interpret(text, repair)
                            proposal = Interpretation.model_validate(proposal.model_dump())
                            supported_observations(text, proposal)
                            analysis = build_analysis(text, proposal)
                            return AnalysisResult(
                                analysis=analysis,
                                model=self.llm.model,
                                attempts=attempt,
                                latency_ms=round((time.monotonic() - started) * 1000),
                            )
                        except (TimeoutError, ProviderTimeoutError):
                            if attempt == 2:
                                raise AnalysisError(
                                    "analysis_timeout",
                                    "Analysis timed out. Please retry or arrange manual review "
                                    "for urgent reports.",
                                    504,
                                ) from None
                        except TransientProviderError:
                            if attempt == 2:
                                raise AnalysisError(
                                    "analysis_unavailable",
                                    "Analysis is temporarily unavailable. Please retry or arrange "
                                    "manual review for urgent reports.",
                                    503,
                                ) from None
                        except ProviderRequestError:
                            raise AnalysisError(
                                "provider_request_rejected",
                                "The analysis provider rejected the request. Check the configured "
                                "credentials and model.",
                                502,
                            ) from None
                        except (InvalidModelOutput, ValidationError, ValueError, AttributeError):
                            if attempt == 2:
                                raise AnalysisError(
                                    "invalid_model_output",
                                    "Analysis could not be validated. "
                                    "Please retry or arrange manual review.",
                                    502,
                                ) from None
                            repair = "invalid_schema_or_unsupported_quote"
        except AnalysisError:
            raise
        except TimeoutError:
            raise AnalysisError(
                "analysis_timeout",
                "Analysis timed out. Please retry or arrange manual review for urgent reports.",
                504,
            ) from None
        except BlockedModelOutput:
            raise AnalysisError(
                "analysis_blocked",
                "Analysis could not be completed for this update. Please arrange manual review.",
                502,
            ) from None
        except Exception:
            # Provider exceptions can contain secrets or input; never expose their text.
            raise AnalysisError(
                "analysis_unavailable",
                "Analysis is temporarily unavailable. "
                "Please retry or arrange manual review for urgent reports.",
                503,
            ) from None
        raise RuntimeError("Analysis completed without a result.")
