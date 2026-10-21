import asyncio

import pytest

from core.config import Settings
from llm.base import (
    BlockedModelOutput,
    InvalidModelOutput,
    ProviderRequestError,
    ProviderTimeoutError,
    TransientProviderError,
)
from schemas import Interpretation, Observation
from services.analysis_service import AnalysisError, AnalysisService
from tests.doubles import ScriptedLLM, configured_settings


@pytest.mark.parametrize(
    "error,code,status,attempts",
    [
        (TimeoutError(), "analysis_timeout", 504, 2),
        (ProviderTimeoutError(), "analysis_timeout", 504, 2),
        (TransientProviderError(), "analysis_unavailable", 503, 2),
        (ProviderRequestError(), "provider_request_rejected", 502, 1),
        (InvalidModelOutput("invalid"), "invalid_model_output", 502, 2),
        (BlockedModelOutput("blocked"), "analysis_blocked", 502, 1),
        (RuntimeError("sensitive provider error"), "analysis_unavailable", 503, 1),
    ],
)
async def test_provider_failure_returns_explicit_error(error, code, status, attempts):
    client = ScriptedLLM(error)
    with pytest.raises(AnalysisError) as caught:
        await AnalysisService(client, configured_settings()).analyze("A customer feels unwell.")
    assert caught.value.code == code
    assert caught.value.status_code == status
    if status in {503, 504}:
        assert "manual review" in caught.value.message
    assert "sensitive" not in caught.value.message
    assert client.calls == attempts


async def test_single_repair_can_produce_validated_analysis():
    client = ScriptedLLM(
        InvalidModelOutput("invalid"),
        Interpretation(
            observations=[Observation(kind="stockout", quote="unavailable")], provided_details=[]
        ),
    )
    result = await AnalysisService(client, configured_settings()).analyze(
        "Indiranagar Mart cola unavailable."
    )
    assert result.attempts == 2
    assert result.analysis.recommended_next_action == "request_restock"
    assert client.repairs == [None, "invalid_schema_or_unsupported_quote"]


@pytest.mark.parametrize("error", [ProviderTimeoutError(), TransientProviderError()])
async def test_transient_provider_failure_can_succeed_on_second_attempt(error):
    client = ScriptedLLM(
        error,
        Interpretation(
            observations=[Observation(kind="stockout", quote="unavailable")],
            provided_details=[],
        ),
    )
    result = await AnalysisService(client, configured_settings()).analyze(
        "Indiranagar Mart cola unavailable."
    )
    assert result.attempts == 2
    assert result.analysis.recommended_next_action == "request_restock"
    assert client.repairs == [None, None]


async def test_fabricated_quote_is_rejected_after_repair():
    client = ScriptedLLM(
        Interpretation(
            observations=[Observation(kind="illness", quote="fabricated")], provided_details=[]
        )
    )
    with pytest.raises(AnalysisError, match="could not be validated") as caught:
        await AnalysisService(client, configured_settings()).analyze(
            "Metro Fresh cola unavailable."
        )
    assert caught.value.code == "invalid_model_output"
    assert client.calls == 2


async def test_async_timeout_and_concurrency_bound():
    class SlowLLM:
        model = "test-boundary"
        active = 0
        maximum = 0

        async def interpret(self, text, repair=None):
            self.active += 1
            self.maximum = max(self.active, self.maximum)
            try:
                await asyncio.sleep(1)
            finally:
                self.active -= 1

    client = SlowLLM()
    service = AnalysisService(
        client,
        configured_settings(
            max_concurrent_analyses=1,
            model_attempt_timeout_seconds=0.01,
            model_total_timeout_seconds=0.02,
        ),
    )
    results = await asyncio.gather(
        *(service.analyze("A customer is sick.") for _ in range(3)),
        return_exceptions=True,
    )
    assert client.maximum == 1
    assert all(
        isinstance(result, AnalysisError) and result.status_code == 504 for result in results
    )


def test_blank_key_fails_startup():
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        Settings(_env_file=None, gemini_api_key=" ")


def test_missing_key_fails_startup(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        Settings(_env_file=None)


def test_selected_groq_provider_requires_its_key():
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        Settings(_env_file=None, llm_provider="groq", gemini_api_key="unused")


def test_unselected_provider_key_is_not_required():
    settings = Settings(_env_file=None, llm_provider="groq", groq_api_key="configured")
    assert settings.gemini_api_key is None


def test_unsupported_provider_is_rejected():
    with pytest.raises(ValueError, match="llm_provider"):
        configured_settings(llm_provider="offline")
