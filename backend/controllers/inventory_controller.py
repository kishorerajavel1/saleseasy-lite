from fastapi import APIRouter

from repositories.inventory_repository import INVENTORY
from schemas.system import InventoryRecord

router = APIRouter(tags=["Inventory"])


@router.get("/inventory", response_model=list[InventoryRecord])
async def inventory() -> list[InventoryRecord]:
    """Serve the same immutable fictional records used by the triage policy."""
    return [
        InventoryRecord(id=r.id, outlet=r.outlet, sku=r.sku, system_stock=r.system_stock)
        for r in INVENTORY
    ]
