import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.AWAKENING_API_INTERNAL_URL ?? "http://127.0.0.1:8000/api/v1";
const HOP_BY_HOP = new Set(["connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade", "host"]);

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = `${API_BASE.replace(/\/$/, "")}/${path.join("/")}${request.nextUrl.search}`;
  const headers = new Headers();
  request.headers.forEach((value, key) => { if (!HOP_BY_HOP.has(key)) headers.set(key, value); });
  const init: RequestInit = { method: request.method, headers, redirect: "manual" };
  if (request.method !== "GET" && request.method !== "HEAD") init.body = await request.arrayBuffer();
  const upstream = await fetch(target, init);
  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => { if (!HOP_BY_HOP.has(key) && key !== "set-cookie") responseHeaders.set(key, value); });
  const setCookies = upstream.headers.getSetCookie?.() ?? [];
  for (const cookie of setCookies) responseHeaders.append("set-cookie", cookie);
  return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
