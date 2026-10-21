from core.config import Settings
from llm.factory import create_llm


def test_factory_selects_gemini(monkeypatch):
    sentinel = object()
    monkeypatch.setattr("llm.factory.GeminiLLM", lambda settings: sentinel)
    settings = Settings(_env_file=None, llm_provider="gemini", gemini_api_key="key")
    assert create_llm(settings) is sentinel


def test_factory_selects_groq(monkeypatch):
    sentinel = object()
    monkeypatch.setattr("llm.factory.GroqLLM", lambda settings: sentinel)
    settings = Settings(_env_file=None, llm_provider="groq", groq_api_key="key")
    assert create_llm(settings) is sentinel
