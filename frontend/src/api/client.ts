/** Cliente HTTP ligero para la API del backend (/api/v1).

Usa fetch nativo. Toda respuesta de error se convierte en una excepción
con el envelope de errores del backend (code/message/details/request_id).
*/

import type { ApiError } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(input, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!res.ok) {
    let error: ApiError = {
      code: "http_error",
      message: `HTTP ${res.status}`,
    };
    try {
      error = (await res.json()) as ApiError;
    } catch {
      // Ignorar si el cuerpo no es JSON.
    }
    throw new Error(error.message, { cause: error });
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(`${API_BASE}${path}`),
  post: <T>(path: string, body?: unknown) =>
    request<T>(`${API_BASE}${path}`, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(`${API_BASE}${path}`, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(`${API_BASE}${path}`, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(path: string) =>
    request<T>(`${API_BASE}${path}`, { method: "DELETE" }),
};
