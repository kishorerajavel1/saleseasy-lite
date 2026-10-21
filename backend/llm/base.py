from typing import Protocol

from schemas import Interpretation


class InvalidModelOutput(Exception):
    """Parsing/schema failure, eligible for one bounded repair."""


class BlockedModelOutput(Exception):
    """Provider refusal/empty output; not treated as a successful analysis."""


class ProviderTimeoutError(Exception):
    """The provider reported that its operation exceeded a deadline."""


class TransientProviderError(Exception):
    """The provider or network failed in a way that may succeed on retry."""


class ProviderRequestError(Exception):
    """The provider rejected the request or configuration; retrying will not help."""


class LLMClient(Protocol):
    provider: str
    model: str

    async def interpret(self, text: str, repair: str | None = None) -> Interpretation: ...
