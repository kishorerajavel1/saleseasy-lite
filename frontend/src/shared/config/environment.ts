/** Frontend deployment configuration. Every VITE_ value is public in the bundle. */
const configuredUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000";
const parsed = new URL(configuredUrl);
if (
  !["http:", "https:"].includes(parsed.protocol) ||
  parsed.username ||
  parsed.password ||
  parsed.search ||
  parsed.hash
) {
  throw new Error(
    "VITE_API_BASE_URL must be an HTTP(S) base URL without credentials, query, or fragment.",
  );
}

export const API_BASE_URL = configuredUrl.replace(/\/$/, "");
export const apiUrl = (path: string): string => `${API_BASE_URL}${path}`;
