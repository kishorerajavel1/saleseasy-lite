import { parseResponse, request } from "../../../shared/api/client";
import {
  inventorySchema,
  type InventoryRecord,
} from "../../../shared/api/contracts";

export async function getInventory(
  signal: AbortSignal,
): Promise<InventoryRecord[]> {
  return parseResponse(
    await request("/inventory", { signal }),
    inventorySchema,
  );
}
