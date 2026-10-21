import pytest

from core.config import Settings
from llm.base import BlockedModelOutput, InvalidModelOutput, ProviderRequestError
from llm.groq import GroqLLM
from schemas import Interpretation


@pytest.fixture
def fake_provider(monkeypatch):
    import langchain_groq

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

        async def ainvoke(self, prompt_messages):
            assert prompt_messages[0]["role"] == "system"
            assert prompt_messages[1]["role"] == "user"
            assert '"field_update"' in prompt_messages[1]["content"]
            return self.result

    monkeypatch.setattr(langchain_groq, "ChatGroq", FakeChat)
    return FakeChat


def groq_settings() -> Settings:
    return Settings(_env_file=None, llm_provider="groq", groq_api_key="test-placeholder")


async def test_provider_uses_strict_native_schema_and_no_hidden_retries(fake_provider):
    adapter = GroqLLM(groq_settings())
    assert fake_provider.config["max_retries"] == 0
    assert fake_provider.config["api_key"].get_secret_value() == "test-placeholder"
    assert fake_provider.call_options == {
        "method": "json_schema",
        "include_raw": True,
        "strict": True,
    }
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
    adapter = GroqLLM(groq_settings())
    with pytest.raises(error):
        await adapter.interpret("A field update.")


async def test_provider_rejection_is_classified(fake_provider):
    class ProviderFailure(Exception):
        status_code = 401

    async def fail(self, prompt_messages):
        raise ProviderFailure()

    fake_provider.ainvoke = fail
    with pytest.raises(ProviderRequestError):
        await GroqLLM(groq_settings()).interpret("A field update.")
