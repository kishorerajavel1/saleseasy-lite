from pydantic import ValidationError

from core.config import Settings
from llm.base import (
    BlockedModelOutput,
    InvalidModelOutput,
)
from llm.prompts import messages
from llm.provider_errors import raise_provider_error
from schemas import Interpretation


class GeminiLLM:
    provider = "gemini"

    def __init__(self, settings: Settings):
        # Lazy import keeps offline tests independent of the provider implementation.
        from langchain_google_genai import ChatGoogleGenerativeAI

        self.model = settings.gemini_model
        self.client = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=settings.gemini_api_key.get_secret_value(),  # type: ignore[union-attr]
            vertexai=False,
            max_retries=0,
            timeout=settings.model_attempt_timeout_seconds,
            max_output_tokens=4096,
        ).with_structured_output(Interpretation, method="json_schema", include_raw=True)

    async def interpret(self, text: str, repair: str | None = None) -> Interpretation:
        try:
            result = await self.client.ainvoke(messages(text, repair))
        except Exception as error:
            raise_provider_error(error)
        if result.get("parsing_error") is not None:
            raise InvalidModelOutput("provider_parse_failed")
        parsed = result.get("parsed")
        if parsed is None:
            raise BlockedModelOutput("provider_empty_or_blocked")
        try:
            if isinstance(parsed, Interpretation):
                return Interpretation.model_validate(parsed.model_dump())
            return Interpretation.model_validate(parsed)
        except ValidationError as error:
            raise InvalidModelOutput("provider_schema_failed") from error
