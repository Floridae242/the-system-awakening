import { describe, expect, it, vi } from "vitest";

import { fetchUpstream } from "../../apps/web/lib/upstream";

describe("fetchUpstream", () => {
  it("retries a transient gateway response for a GET", async () => {
    const cancel = vi.fn();
    const gatewayBody = new ReadableStream<Uint8Array>({ cancel });
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(new Response(gatewayBody, { status: 502 }))
      .mockResolvedValueOnce(new Response('{"success":true}', { status: 200 }));

    const response = await fetchUpstream("https://api.example.test/player", { method: "GET" }, fetcher, 0);

    expect(response.status).toBe(200);
    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(cancel).toHaveBeenCalledOnce();
  });

  it("does not replay a state-changing request", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response("bad gateway", { status: 502 }));

    const response = await fetchUpstream("https://api.example.test/quests", { method: "POST" }, fetcher, 0);

    expect(response.status).toBe(502);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("does not replay login because it creates a session", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response("unavailable", { status: 503 }));

    const response = await fetchUpstream("https://api.example.test/auth/login", { method: "POST" }, fetcher, 0);

    expect(response.status).toBe(503);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("aborts a stalled upstream attempt", async () => {
    const fetcher = vi.fn<typeof fetch>((_input, init) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(init.signal?.reason), { once: true });
    }));

    await expect(fetchUpstream("https://api.example.test/player", { method: "POST" }, fetcher, 0, 5)).rejects.toBeDefined();
  });

  it("rejects a chunked body that grows beyond its limit", async () => {
    const { PayloadTooLargeError, readBodyWithLimit } = await import("../../apps/web/lib/upstream");
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new Uint8Array(4));
        controller.enqueue(new Uint8Array(4));
        controller.close();
      },
    });

    await expect(readBodyWithLimit(body, 6)).rejects.toBeInstanceOf(PayloadTooLargeError);
  });
});
