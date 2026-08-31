import { NextRequest, NextResponse } from "next/server";

import { copyUpstreamHeaders, fetchUpstream, maxBodyBytes, PayloadTooLargeError, readBodyWithLimit } from "../../../../lib/upstream";

const API_BASE = process.env.AWAKENING_API_INTERNAL_URL ?? "http://127.0.0.1:8000/api/v1";
const HOP_BY_HOP = new Set(["connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade", "host"]);
const REQUEST_HEADERS = new Set(["accept", "authorization", "content-type", "cookie", "idempotency-key", "x-csrf-token"]);

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = `${API_BASE.replace(/\/$/, "")}/${path.join("/")}${request.nextUrl.search}`;
  const headers = new Headers();
  request.headers.forEach((value, key) => { if (REQUEST_HEADERS.has(key) && !HOP_BY_HOP.has(key)) headers.set(key, value); });
  const init: RequestInit = { method: request.method, headers, redirect: "manual", cache: "no-store", signal: request.signal };
  if (request.method !== "GET" && request.method !== "HEAD") {
    const limit = maxBodyBytes(request.headers.get("content-type"));
    const declaredLength = Number(request.headers.get("content-length") ?? 0);
    if (Number.isFinite(declaredLength) && declaredLength > limit) {
      return NextResponse.json({ detail: "Request body exceeds the allowed limit" }, { status: 413 });
    }
    try {
      init.body = await readBodyWithLimit(request.body, limit);
    } catch (error) {
      if (error instanceof PayloadTooLargeError) {
        return NextResponse.json({ detail: error.message }, { status: 413 });
      }
      throw error;
    }
  }
  let upstream: Response;
  try {
    upstream = await fetchUpstream(target, init);
  } catch {
    return NextResponse.json({ detail: "Upstream service temporarily unavailable" }, { status: 502 });
  }
  const responseHeaders = copyUpstreamHeaders(upstream.headers);
  const setCookies = upstream.headers.getSetCookie?.() ?? [];
  for (const cookie of setCookies) responseHeaders.append("set-cookie", cookie);
  return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
