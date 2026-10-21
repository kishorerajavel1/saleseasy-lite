"""Conservative safety signals that supplement validated LLM interpretations."""

import re

from domain.text_normalization import normalize
from schemas import Observation, ProvidedDetail

PATTERNS = {
    "illness": r"\b(?:unwell|sick|ill|vomit(?:ing|ed)?|nausea|diarrh[oe]+a|hospitali[sz]ed|"
    r"allergic reaction|feeling faint|stomach pain|food poisoning)\b",
    "hazard": r"\b(?:contaminat\w*|tamper(?:ed|ing)?|foreign object|choking|"
    r"glass (?:shard|fragment)s?|swollen pack|chemical smell)\b",
    "damage": r"\b(?:damaged?|broken|leak(?:ing|s)?|expired|torn|crushed)\b",
    "stockout": r"\b(?:out[ -]of[ -]stock|stockout|unavailable|not available|"
    r"no stock|zero stock|shelf (?:is )?empty|empty shel(?:f|ves)|"
    r"(?:cola|juice) (?:is )?finished|ran out)\b",
    "in_stock": r"\b(?:in stock|plenty (?:of stock|available)|"
    r"stock (?:is )?available|well stocked)\b",
    "low_stock": r"\b(?:low stock|stock (?:is |running )?low|running low|few units left)\b",
    "pricing": r"\b(?:discount(?:ing|s|ed)?|price[ -]match|match (?:their |the )?price|"
    r"match their pricing|undercut(?:ting)?|cut (?:the )?price)\b",
    "commercial": r"\b(?:refund|credit note|commercial concession|approve (?:the )?order)\b",
    "impact": r"\b(?:lost sales|losing (?:\w+ ){0,4}sales|major sales|huge sales|"
    r"lost revenue|revenue loss|sales loss|loss of sales)\b",
}
INJECTION = re.compile(
    r"\b(?:ignore|disregard|override)\b.{0,65}\b(?:instructions?|rules?|policy|prompt)\b"
    r"|\bsystem\s*:|\byou are now\b|\bact as\b|\bsystem prompt\b"
    r"|\bmark\b.{0,35}\bresolved\b|\bset\b.{0,25}\burgency\b.{0,15}\blow\b"
    r"|\bignora\b.{0,45}\binstrucciones\b",
    re.DOTALL,
)
IRRELEVANT = re.compile(
    r"^\s*(?:(?:hi|hello|hey|good (?:morning|afternoon|evening))(?:\s+(?:there|team))?"
    r"|(?:thanks|thank you)(?:\s+(?:so much|team))?|how are you)\s*[.!?]*\s*$",
    re.I,
)


def negated(text: str, start: int, kind: str, matched: str) -> bool:
    # Negation is local to a clause, never a global 'no' anywhere in the update.
    if kind == "stockout" and re.search(r"\b(?:no stock|not available)\b", matched, re.I):
        return False
    # Model quotes can include their own negator, unlike regex matches that start
    # at the positive keyword. Inspect only text before the keyword in that quote.
    quoted_keyword = re.search(PATTERNS.get(kind, r"(?!)"), matched, re.I)
    inside_prefix = matched[: quoted_keyword.start()] if quoted_keyword else ""
    prefix = re.split(
        r"[.!?;,\n]|\b(?:but|however)\b",
        text[:start] + inside_prefix,
        flags=re.I,
    )[-1]
    words = re.findall(r"\w+", prefix.casefold())[-5:]
    context = " ".join(words)
    if re.search(r"\bnot (?:sure|certain|only)\b", context):
        return False
    return bool(re.search(r"\b(?:no|not|never|nobody|none|without|denies|denied)\b", context))


def detect(text: str) -> list[Observation]:
    observations: list[Observation] = []
    for kind, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text, flags=re.I):
            if not negated(text, match.start(), kind, match.group()):
                observations.append(Observation(kind=kind, quote=match.group()))
                break
    # Obfuscation normalization is ONLY for attack detection, never inventory or evidence.
    attack_text = normalize(text).translate(str.maketrans({"1": "i", "0": "o", "3": "e", "@": "a"}))
    if INJECTION.search(attack_text):
        observations.append(Observation(kind="injection", quote=text))
    if not observations and IRRELEVANT.fullmatch(text):
        observations.append(Observation(kind="irrelevant", quote=text))
    return observations


def detect_details(text: str) -> list[ProvidedDetail]:
    patterns = {
        "competitor_name": r"\bcompetitor\s+"
        r"(?!(?:is|has|was|are|discounting|prices?)\b)[A-Z][\w-]+",
        "observed_price": r"(?:₹\s*\d+(?:\.\d+)?|\b(?:Rs\.?|INR)\s*\d+(?:\.\d+)?)",
        "locations": r"\b(?:at|in)\s+(?:Indiranagar|Koramangala|Bengaluru|"
        r"Bangalore|Metro Fresh|City Corner)\b",
        "proof": r"\b(?:photo|receipt|screenshot|proof)\s+(?:attached|provided|available)\b",
    }
    details = []
    for name, pattern in patterns.items():
        match = re.search(pattern, text, re.I)
        if match:
            details.append(ProvidedDetail(name=name, quote=match.group()))
    return details
