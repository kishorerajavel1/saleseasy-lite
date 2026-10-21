import { useEffect, useRef, useState } from "react";
import type { Result } from "../../../shared/api/contracts";
import { analyzeUpdate } from "../api/triageApi";

/** Owns the analysis interaction lifecycle, not the component tree. */
export function useTriageAnalysis(limit: number) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const active = useRef<AbortController | null>(null);
  useEffect(() => () => active.current?.abort(), []);

  function changeText(value: string) {
    setText(value);
    setResult(null);
    setError("");
  }

  async function analyze() {
    if (active.current || !text.trim() || text.length > limit) return;
    const controller = new AbortController();
    active.current = controller;
    setBusy(true);
    setError("");
    setResult(null);
    // Allow the backend's 45-second retry budget plus network overhead.
    const timeout = window.setTimeout(() => controller.abort(), 50000);
    try {
      setResult(await analyzeUpdate(text, controller.signal));
    } catch (error) {
      setError(
        error instanceof Error && error.name !== "AbortError"
          ? error.message
          : "The request timed out. Please try again; no business action was taken.",
      );
    } finally {
      window.clearTimeout(timeout);
      active.current = null;
      setBusy(false);
    }
  }

  return {
    text,
    changeText,
    result,
    clearResult: () => setResult(null),
    busy,
    error,
    dismissError: () => setError(""),
    analyze,
  };
}
