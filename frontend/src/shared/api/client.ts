import { apiUrl } from "../config/environment";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number = 0,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Shared transport; feature clients own response contracts and header interpretation. */
export async function request(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), { ...options, credentials: "omit" });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new ApiError(
      "Cannot reach the API. Check that the backend is running and its CORS origins match this frontend.",
    );
  }
  if (response.ok) return response;
  if (response.status === 429) {
    throw new ApiError(
      `Analysis limit reached. Try again in ${response.headers.get("Retry-After") ?? "60"} seconds.`,
      429,
    );
  }
  if ([413, 422].includes(response.status)) {
    throw new ApiError(
      "Check your update: enter plain text within the character limit, without unsupported control characters.",
      response.status,
    );
  }
  if (response.status === 504) {
    throw new ApiError(
      "Analysis timed out. Please retry or arrange manual review for urgent reports.",
      504,
    );
  }
  if ([502, 503].includes(response.status)) {
    throw new ApiError(
      "Analysis is unavailable or could not be validated. Please retry or arrange manual review for urgent reports.",
      response.status,
    );
  }
  throw new ApiError(
    "The service could not complete this request. Please try again.",
    response.status,
  );
}

export async function parseResponse<T>(
  response: Response,
  schema: { parse(value: unknown): T },
): Promise<T> {
  try {
    return schema.parse(await response.json());
  } catch {
    throw new ApiError(
      "The API returned an invalid response. No business action was taken.",
    );
  }
}
