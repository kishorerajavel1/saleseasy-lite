"""Resolve explicit catalog aliases without fuzzy verification."""

import re
from dataclasses import dataclass

from domain.text_normalization import contains_alias, normalize
from repositories.inventory_repository import (
    INVENTORY,
    OUTLET_ALIASES,
    SKU_ALIASES,
    InventoryRow,
)


@dataclass(frozen=True)
class Resolution:
    outlets: tuple[str, ...]
    skus: tuple[str, ...]
    row: InventoryRow | None

    @property
    def ambiguous(self) -> bool:
        return len(self.outlets) > 1 or len(self.skus) > 1


def resolve(text: str) -> Resolution:
    normalized = normalize(text)
    outlets = tuple(
        k
        for k, aliases in OUTLET_ALIASES.items()
        if any(contains_alias(normalized, a) for a in aliases)
    )
    skus = tuple(
        k
        for k, aliases in SKU_ALIASES.items()
        if any(contains_alias(normalized, a) for a in aliases)
    )
    # Generic aliases must not silently turn an explicitly different pack into a
    # verified SKU (e.g. 'cola 2L' must never resolve to 'Cola 500ml').
    pack_aliases = {"Cola 500ml": ("500ml", "500 ml"), "Juice 1L": ("1l", "1 l")}
    compatible = []
    for sku in skus:
        product = "cola" if sku == "Cola 500ml" else "juice"
        sizes = re.findall(r"\b" + product + r"\s+(\d+(?:\.\d+)?\s*(?:ml|l))\b", normalized)
        if not sizes or all(size in pack_aliases[sku] for size in sizes):
            compatible.append(sku)
    skus = tuple(compatible)
    row = None
    if len(outlets) == len(skus) == 1:
        row = next((r for r in INVENTORY if r.outlet == outlets[0] and r.sku == skus[0]), None)
    return Resolution(outlets, skus, row)
