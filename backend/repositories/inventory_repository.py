"""Read-only fictional catalog; replace this data source when integrating a real system."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryRow:
    id: str
    outlet: str
    sku: str
    system_stock: int

    @property
    def reference(self) -> str:
        return f"{self.id}: {self.outlet} | {self.sku} | system_stock={self.system_stock} units"


INVENTORY = (
    InventoryRow("inv-001", "Indiranagar Mart", "Cola 500ml", 0),
    InventoryRow("inv-002", "Metro Fresh", "Cola 500ml", 48),
    InventoryRow("inv-003", "City Corner", "Juice 1L", 12),
)
OUTLET_ALIASES = {
    "Indiranagar Mart": ("indiranagar mart",),
    "Metro Fresh": ("metro fresh",),
    "City Corner": ("city corner",),
}
SKU_ALIASES = {
    "Cola 500ml": ("cola 500ml", "cola 500 ml", "cola"),
    "Juice 1L": ("juice 1l", "juice 1 l", "juice"),
}
