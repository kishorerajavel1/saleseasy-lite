"""Scripted network boundary for unit tests, never an application provider."""

from core.config import Settings
from schemas import Interpretation


def configured_settings(**overrides) -> Settings:
    return Settings(_env_file=None, gemini_api_key="test-placeholder", **overrides)


class ScriptedLLM:
    provider = "gemini"
    model = "test-boundary"

    def __init__(self, *responses: Interpretation | Exception):
        self.responses = responses or (Interpretation(observations=[], provided_details=[]),)
        self.calls = 0
        self.repairs: list[str | None] = []

    async def interpret(self, text: str, repair: str | None = None) -> Interpretation:
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        self.repairs.append(repair)
        if isinstance(response, Exception):
            raise response
        return response
