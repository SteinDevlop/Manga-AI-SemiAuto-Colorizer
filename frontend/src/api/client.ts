/** Cliente HTTP ligero para la API del backend (/api/v1).
 *
 * Usa fetch nativo. Toda respuesta de error se convierte en una excepción
 * con el envelope de errores del backend (code/message/details/request_id).
 */

import type { ApiError } from "../types";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

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
  listProjects: () => request<Array<{
    id: string;
    nombre: string;
    descripcion: string | null;
    created_at: string | null;
    updated_at: string | null;
    tipo: string | null;
    portada: string | null;
    current_stage: string;
    status: string;
    progreso: number;
  }>>(`${API_BASE}/projects`),
  createProject: (nombre: string, descripcion?: string) =>
    request<{ id: string; nombre: string; descripcion: string | null; created_at: string }>(`${API_BASE}/projects`, {
      method: "POST",
      body: JSON.stringify({ nombre, descripcion }),
    }),
  deleteProject: (projectId: string) =>
    request<void>(`${API_BASE}/projects/${projectId}`, {
      method: "DELETE",
    }),
  getProject: (projectId: string) =>
    request<{
      id: string;
      nombre: string;
      descripcion: string | null;
      tipo: string | null;
      portada: string | null;
      current_stage: string;
      status: string;
      stage_progress: string[];
      progreso: number;
      created_at: string | null;
      updated_at: string | null;
      pages: Array<{
        page_id: string;
        nombre_archivo_original: string;
        ruta_archivo: string;
        estado: string;
        analysis_id: string | null;
        analysis_estado: string | null;
        created_at: string | null;
      }>;
    }>(`${API_BASE}/projects/${projectId}`),
  transitionStage: (projectId: string, action: string, stage: string) =>
    request<{
      project_id: string;
      action: string;
      stage: string;
      current_stage: string;
      status: string;
      stage_progress: string[];
      progreso: number;
    }>(`${API_BASE}/projects/${projectId}/stage`, {
      method: "PATCH",
      body: JSON.stringify({ action, stage }),
    }),
  getMetrics: () =>
    request<{
      total_proyectos: number;
      proyectos_por_estado: Record<string, number>;
      proyectos_por_etapa: Record<string, number>;
      jobs: {
        total: number;
        activos: number;
        completados: number;
        fallidos: number;
      };
      ultimos_proyectos: Array<{
        id: string;
        nombre: string;
        current_stage: string;
        status: string;
        portada: string | null;
        updated_at: string | null;
      }>;
    }>(`${API_BASE}/metrics`),
  listColorizations: () =>
    request<Array<{
      job_id: string;
      analysis_id: string;
      estado: string;
      progreso: number;
      mensaje: string | null;
      ruta_resultado: string | null;
      version_modelo: string | null;
      created_at: string | null;
      updated_at: string | null;
    }>>(`${API_BASE}/colorizations`),
  uploadFile: (formData: FormData) =>
    request<{ id: string; project_id: string; nombre_archivo_original: string; hash_sha256: string; ruta_archivo: string; mime_type: string | null; ancho: number | null; alto: number | null; tamano_bytes: number; estado: string; created_at: string }>(`${API_BASE}/pages`, {
      method: "POST",
      body: formData,
      // No establecer Content-Type; el navegador lo pone con el boundary de FormData
      headers: {},
    }),
};
