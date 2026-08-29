const API_ROOT = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

interface Envelope<T> {
  success: true;
  data: T;
}

export async function api<T>(
  path: string,
  options: RequestInit & { token?: string; idempotencyKey?: string } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);
  if (options.idempotencyKey) headers.set("Idempotency-Key", options.idempotencyKey);
  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers });
  const payload = (await response.json().catch(() => null)) as Envelope<T> | { detail?: string } | null;
  if (!response.ok) {
    const message = payload && "detail" in payload ? payload.detail : undefined;
    throw new Error(message || `Request failed (${response.status})`);
  }
  return (payload as Envelope<T>).data;
}
