const TRANSIENT_GATEWAY_STATUSES = new Set([502, 503, 504]);
const UNSAFE_RESPONSE_HEADERS = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

type Fetcher = (input: string | URL | Request, init?: RequestInit) => Promise<Response>;

export class PayloadTooLargeError extends Error {}

function canRetry(target: string, method = "GET") {
  const normalizedMethod = method.toUpperCase();
  return normalizedMethod === "GET" || normalizedMethod === "HEAD";
}

function wait(delayMs: number) {
  return delayMs > 0 ? new Promise((resolve) => setTimeout(resolve, delayMs)) : Promise.resolve();
}

export async function fetchUpstream(
  target: string,
  init: RequestInit,
  fetcher: Fetcher = fetch,
  retryDelayMs = 300,
  timeoutMs = 8_000,
) {
  const retryable = canRetry(target, init.method);
  const attempt = () => {
    const timeoutSignal = AbortSignal.timeout(timeoutMs);
    const signal = init.signal ? AbortSignal.any([init.signal, timeoutSignal]) : timeoutSignal;
    return fetcher(target, { ...init, signal });
  };

  try {
    const response = await attempt();
    if (!retryable || !TRANSIENT_GATEWAY_STATUSES.has(response.status)) return response;
    await response.body?.cancel().catch(() => undefined);
  } catch (error) {
    if (!retryable) throw error;
  }

  await wait(retryDelayMs);
  return attempt();
}

export function maxBodyBytes(contentType: string | null) {
  return contentType?.toLowerCase().startsWith("multipart/form-data") ? 8 * 1024 * 1024 + 16_384 : 16_384;
}

export async function readBodyWithLimit(body: ReadableStream<Uint8Array> | null, limit: number) {
  if (!body) return undefined;
  const reader = body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) {
        await reader.cancel();
        throw new PayloadTooLargeError("Request body exceeds the allowed limit");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const combined = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    combined.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return combined;
}

export function copyUpstreamHeaders(source: Headers) {
  const headers = new Headers();
  source.forEach((value, key) => {
    if (!UNSAFE_RESPONSE_HEADERS.has(key) && key !== "set-cookie") headers.set(key, value);
  });
  return headers;
}
