import { useEffect, useState } from "react";
import type { Health } from "../../../shared/api/contracts";
import { getServiceHealth } from "../api/triageApi";

export function useServiceHealth() {
  const [health, setHealth] = useState<Health | null>(null);
  const [offline, setOffline] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    getServiceHealth(controller.signal)
      .then(setHealth)
      .catch((error) => {
        if (error.name !== "AbortError") setOffline(true);
      });
    return () => controller.abort();
  }, []);
  return { health, offline };
}
