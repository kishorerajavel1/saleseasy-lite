"""Translate provider SDK failures into the application's stable error contract."""

from llm.base import ProviderRequestError, ProviderTimeoutError, TransientProviderError


def raise_provider_error(error: Exception) -> None:
    status = provider_status(error)
    if status in {408, 504}:
        raise ProviderTimeoutError from error
    if status == 429 or (status is not None and 500 <= status <= 599):
        raise TransientProviderError from error
    if status in {400, 401, 403, 404, 409, 422}:
        raise ProviderRequestError from error
    # Connection resets, DNS failures and other transport errors generally have
    # no HTTP status and may succeed on the bounded second attempt.
    raise TransientProviderError from error


def provider_status(error: Exception) -> int | None:
    """Read a structured status from wrapped SDK errors without parsing messages."""
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        for attribute in ("code", "status_code", "status"):
            value = getattr(current, attribute, None)
            if isinstance(value, int):
                return value
        response = getattr(current, "response", None)
        value = getattr(response, "status_code", None)
        if isinstance(value, int):
            return value
        current = current.__cause__ or current.__context__
    return None
