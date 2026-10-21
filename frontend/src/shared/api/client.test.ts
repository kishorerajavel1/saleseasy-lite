import { describe, expect, it, vi } from "vitest";
import { ApiError, parseResponse, request } from "./client";
import { analysisSchema } from "./contracts";
import { API_BASE_URL } from "../config/environment";
import { analyzeUpdate } from "../../features/triage/api/triageApi";

describe("frontend API boundary", () => {
  it("uses the configured backend origin without sending credentials", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(Response.json({}));
    await request("/health");
    expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/health`, {
      credentials: "omit",
    });
  });

  it("rejects a malformed analysis instead of crashing a presentation component", async () => {
    await expect(
      parseResponse(Response.json({ urgency: "not-an-enum" }), analysisSchema),
    ).rejects.toThrow("invalid response");
  });

  it("rejects an invalid analysis response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({}));
    await expect(
      analyzeUpdate("an update", new AbortController().signal),
    ).rejects.toThrow("invalid response");
  });

  it("turns network/CORS failures into an actionable error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(
      new TypeError("Failed to fetch"),
    );
    await expect(request("/health")).rejects.toBeInstanceOf(ApiError);
    await expect(request("/health")).rejects.toThrow("CORS origins");
  });
});
