// Browser requests go through the Next BFF. The API URL is server-only in
// production, so session cookies never need to be exposed to JavaScript.
// Browser traffic always terminates at the same-origin BFF. The upstream API
// URL is server-only (`AWAKENING_API_INTERNAL_URL`) and never bundled.
const API_ROOT = "/api/backend";

interface Envelope<T> {
  success: true;
  data: T;
}

function isEnvelope<T>(value: unknown): value is Envelope<T> {
  return Boolean(value && typeof value === "object" && "data" in value);
}

export async function api<T>(
  path: string,
  options: RequestInit & { token?: string; idempotencyKey?: string } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);
  if (options.idempotencyKey) headers.set("Idempotency-Key", options.idempotencyKey);
  if (options.method && options.method !== "GET" && options.method !== "HEAD") {
    const csrf = document.cookie.match(/(?:^|; )awakening_csrf=([^;]+)/)?.[1];
    if (csrf) headers.set("X-CSRF-Token", decodeURIComponent(csrf));
  }
  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers, credentials: "include" });
  const payload = (await response.json().catch(() => null)) as Envelope<T> | { detail?: string } | null;
  if (!response.ok) {
    const message = payload && typeof payload === "object" && "detail" in payload ? payload.detail : undefined;
    throw new Error(message || `Request failed (${response.status})`);
  }
  if (!isEnvelope<T>(payload)) {
    throw new Error(`Invalid API response (${response.status})`);
  }
  return payload.data;
}
