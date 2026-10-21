import pytest

from core.config import Settings
from llm.base import (
    BlockedModelOutput,
    InvalidModelOutput,
    ProviderRequestError,
    ProviderTimeoutError,
    TransientProviderError,
)
from llm.gemini import GeminiLLM
from schemas import Interpretation


@pytest.fixture
def fake_provider(monkeypatch):
    import langchain_google_genai

    class FakeChat:
        config = None
        schema = None
        call_options = None
        result = {"parsed": Interpretation(observations=[], provided_details=[])}

        def __init__(self, **kwargs):
            FakeChat.config = kwargs

        def with_structured_output(self, schema, **kwargs):
            FakeChat.schema = schema
            FakeChat.call_options = kwargs
            return self

        async def ainvoke(self, messages):
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert '"field_update"' in messages[1]["content"]
            return self.result

    monkeypatch.setattr(langchain_google_genai, "ChatGoogleGenerativeAI", FakeChat)
    return FakeChat


async def test_provider_uses_native_schema_and_no_hidden_retries(fake_provider):
    settings = Settings(_env_file=None, llm_provider="gemini", gemini_api_key="test-placeholder")
    adapter = GeminiLLM(settings)
    assert fake_provider.config["max_retries"] == 0
    assert fake_provider.config["vertexai"] is False
    assert "temperature" not in fake_provider.config
    assert fake_provider.call_options == {"method": "json_schema", "include_raw": True}
    assert fake_provider.schema is Interpretation
    assert await adapter.interpret("City Corner juice.") == Interpretation(
        observations=[], provided_details=[]
    )


@pytest.mark.parametrize(
    "result,error",
    [
        ({"parsed": None}, BlockedModelOutput),
        ({"parsing_error": ValueError("bad JSON")}, InvalidModelOutput),
        (
            {"parsed": {"observations": [], "provided_details": [], "extra": "forbidden"}},
            InvalidModelOutput,
        ),
    ],
)
async def test_provider_invalid_and_blocked_outputs(fake_provider, result, error):
    fake_provider.result = result
    adapter = GeminiLLM(
        Settings(_env_file=None, llm_provider="gemini", gemini_api_key="test-placeholder")
    )
    with pytest.raises(error):
        await adapter.interpret("A field update.")


@pytest.mark.parametrize(
    "status,error",
    [
        (400, ProviderRequestError),
        (401, ProviderRequestError),
        (403, ProviderRequestError),
        (404, ProviderRequestError),
        (429, TransientProviderError),
        (500, TransientProviderError),
        (503, TransientProviderError),
        (504, ProviderTimeoutError),
    ],
)
async def test_provider_errors_are_classified_by_structured_status(fake_provider, status, error):
    class ProviderFailure(Exception):
        def __init__(self, code):
            self.code = code

    async def fail(self, messages):
        raise ProviderFailure(status)

    fake_provider.ainvoke = fail
    adapter = GeminiLLM(
        Settings(_env_file=None, llm_provider="gemini", gemini_api_key="test-placeholder")
    )
    with pytest.raises(error):
        await adapter.interpret("A field update.")


async def test_wrapped_provider_status_is_discovered(fake_provider):
    class ProviderFailure(Exception):
        code = 504

    async def fail(self, messages):
        try:
            raise ProviderFailure()
        except ProviderFailure as error:
            raise RuntimeError("wrapper without status") from error

    fake_provider.ainvoke = fail
    adapter = GeminiLLM(
        Settings(_env_file=None, llm_provider="gemini", gemini_api_key="test-placeholder")
    )
    with pytest.raises(ProviderTimeoutError):
        await adapter.interpret("A field update.")
