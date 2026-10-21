"""Select the configured real LLM provider at application startup."""

from core.config import Settings
from llm.base import LLMClient
from llm.gemini import GeminiLLM
from llm.groq import GroqLLM


def create_llm(settings: Settings) -> LLMClient:
    if settings.llm_provider == "groq":
        return GroqLLM(settings)
    return GeminiLLM(settings)
