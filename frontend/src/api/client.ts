const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function getToken(): string | null {
  return localStorage.getItem("sh_access_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("sh_access_token", access);
  localStorage.setItem("sh_refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("sh_access_token");
  localStorage.removeItem("sh_refresh_token");
}

async function tryRefresh(): Promise<string | null> {
  const refresh = localStorage.getItem("sh_refresh_token");
  if (!refresh) return null;
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, init: RequestInit = {}, retried = false): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });
  if (res.status === 401 && token && !retried) {
    const next = await tryRefresh();
    if (next) return api<T>(path, init, true);
    clearTokens();
  }
  if (!res.ok) {
    let message = "Что-то пошло не так. Мы уже чиним. Попробуйте обновить страницу.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") message = data.detail;
    } catch {
      /* keep default */
    }
    throw new ApiError(res.status, message);
  }
  if (res.status === 204) return {} as T;
  return (await res.json()) as T;
}

export const get = <T>(path: string) => api<T>(path);
export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
export const patch = <T>(path: string, body: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
export const del = <T>(path: string) => api<T>(path, { method: "DELETE" });
