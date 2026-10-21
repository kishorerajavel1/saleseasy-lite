from typing import Literal

from pydantic import Field

from schemas.analysis import StrictModel

Signal = Literal[
    "illness",
    "hazard",
    "damage",
    "stockout",
    "in_stock",
    "pricing",
    "commercial",
    "impact",
    "injection",
    "low_stock",
    "routine",
    "irrelevant",
]
DetailName = Literal["competitor_name", "sku", "observed_price", "locations", "proof"]


class Observation(StrictModel):
    kind: Signal
    quote: str = Field(min_length=1, max_length=2000, description="Exact original input substring")


class ProvidedDetail(StrictModel):
    name: DetailName
    quote: str = Field(
        min_length=1, max_length=2000, description="Exact supporting input substring"
    )


class Interpretation(StrictModel):
    """The model labels quoted observations; it cannot verify facts or authorize actions."""

    observations: list[Observation] = Field(max_length=12)
    provided_details: list[ProvidedDetail] = Field(max_length=5)
