const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  code: string;
  requestId: string;
  status: number;

  constructor(status: number, code: string, message: string, requestId: string) {
    super(message);
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

const TOKEN_KEY = "contractlens_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

interface RequestOptions extends RequestInit {
  auth?: boolean;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const finalHeaders = new Headers(headers);
  // Let the browser set the multipart boundary itself for FormData bodies.
  if (!(rest.body instanceof FormData)) {
    finalHeaders.set("Content-Type", "application/json");
  }

  if (auth) {
    const token = getToken();
    if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, { ...rest, headers: finalHeaders });

  if (!response.ok) {
    let code = "UNKNOWN_ERROR";
    let message = "Something went wrong. Please try again.";
    let requestId = "unknown";
    try {
      const body = await response.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
      requestId = body?.error?.request_id ?? requestId;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, code, message, requestId);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
