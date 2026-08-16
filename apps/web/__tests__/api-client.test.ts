import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { apiFetch, ApiError, clearToken, getToken, setToken } from "@/lib/api-client";

describe("api-client token storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  test("getToken returns null when nothing stored", () => {
    expect(getToken()).toBeNull();
  });

  test("setToken then getToken round-trips the value", () => {
    setToken("abc123");
    expect(getToken()).toBe("abc123");
  });

  test("clearToken removes the stored value", () => {
    setToken("abc123");
    clearToken();
    expect(getToken()).toBeNull();
  });
});

describe("apiFetch", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  test("parses a successful JSON response", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ hello: "world" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const result = await apiFetch<{ hello: string }>("/ping");
    expect(result).toEqual({ hello: "world" });
  });

  test("returns undefined for a 204 No Content response", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(null, { status: 204 })
    );

    const result = await apiFetch<undefined>("/ping");
    expect(result).toBeUndefined();
  });

  test("throws an ApiError with code/message/requestId from an error response", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "NOT_FOUND",
            message: "Document not found.",
            request_id: "req-123",
          },
        }),
        { status: 404, headers: { "Content-Type": "application/json" } }
      )
    );

    await expect(apiFetch("/documents/missing")).rejects.toMatchObject({
      status: 404,
      code: "NOT_FOUND",
      message: "Document not found.",
      requestId: "req-123",
    });
  });

  test("throws a fallback ApiError when the error response has no JSON body", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response("not json", { status: 500 })
    );

    let caught: unknown;
    try {
      await apiFetch("/boom");
    } catch (err) {
      caught = err;
    }
    expect(caught).toBeInstanceOf(ApiError);
    expect((caught as ApiError).code).toBe("UNKNOWN_ERROR");
    expect((caught as ApiError).status).toBe(500);
  });

  test("attaches the Authorization header when a token is present and auth is requested", async () => {
    setToken("my-token");
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({}), { status: 200 })
    );

    await apiFetch("/me");

    const [, requestInit] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const headers = requestInit.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer my-token");
  });

  test("omits the Authorization header when auth: false is passed", async () => {
    setToken("my-token");
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({}), { status: 200 })
    );

    await apiFetch("/public", { auth: false });

    const [, requestInit] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const headers = requestInit.headers as Headers;
    expect(headers.get("Authorization")).toBeNull();
  });

  test("omits the Authorization header when no token is stored", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({}), { status: 200 })
    );

    await apiFetch("/me");

    const [, requestInit] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const headers = requestInit.headers as Headers;
    expect(headers.get("Authorization")).toBeNull();
  });
});
