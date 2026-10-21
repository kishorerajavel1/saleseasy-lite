import re
import unicodedata


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return " ".join(text.casefold().split())


def contains_alias(text: str, alias: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text) is not None
