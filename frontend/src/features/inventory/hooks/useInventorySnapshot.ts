import { useEffect, useState } from "react";
import type { InventoryRecord } from "../../../shared/api/contracts";
import { getInventory } from "../api/inventoryApi";

export function useInventorySnapshot() {
  const [records, setRecords] = useState<InventoryRecord[] | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    getInventory(controller.signal)
      .then(setRecords)
      .catch((error) => {
        if (error.name !== "AbortError")
          setError("Inventory snapshot is unavailable.");
      });
    return () => controller.abort();
  }, []);
  return { records, error };
}
