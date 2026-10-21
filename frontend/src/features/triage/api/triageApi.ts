import { parseResponse, request } from "../../../shared/api/client";
import {
  analysisSchema,
  healthSchema,
  type Health,
  type Result,
} from "../../../shared/api/contracts";

export async function getServiceHealth(signal: AbortSignal): Promise<Health> {
  return parseResponse(await request("/health", { signal }), healthSchema);
}

export async function analyzeUpdate(
  text: string,
  signal: AbortSignal,
): Promise<Result> {
  const response = await request("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal,
  });
  return {
    data: await parseResponse(response, analysisSchema),
  };
}
