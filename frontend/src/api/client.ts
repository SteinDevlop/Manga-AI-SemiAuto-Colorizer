/** Cliente HTTP ligero para la API del backend (/api/v1).
 *
 * Usa fetch nativo con timeout y reintentos de sesión. Toda respuesta de
 * error se convierte en una excepción con el envelope de errores del
 * backend (code/message/details/request_id).
 */

import type { ApiError } from "../types";
import { authToken } from "./auth";

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

/** Tiempo máximo de espera para cada petición (ms). Evita que la UI se quede
 * colgada para siempre si el backend no responde. */
const REQUEST_TIMEOUT_MS = 15000;

async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  // Content-Type solo cuando hay cuerpo JSON: en GET provocaría un preflight
  // CORS (OPTIONS) innecesario en cada petición. FormData fija su boundary.
  const hasJsonBody = typeof init?.body === "string";
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(input, {
      ...init,
      signal: controller.signal,
      headers: {
        ...(hasJsonBody ? { "Content-Type": "application/json" } : {}),
        ...(authToken.get() ? { Authorization: `Bearer ${authToken.get()}` } : {}),
        ...(init?.headers ?? {}),
      },
    });

    if (res.status === 401 && authToken.get()) {
      authToken.clear();
      if (typeof window !== "undefined") window.dispatchEvent(new Event("sumi:unauthorized"));
    }

    if (!res.ok) {
      let error: ApiError = {
        code: "http_error",
        message: `HTTP ${res.status}`,
      };
      try {
        const body = await res.json();
        const d = body?.detail && typeof body.detail === "object" ? body.detail : body;
        error = {
          code: d?.code ?? "http_error",
          message: typeof d?.message === "string" ? d.message : typeof body?.detail === "string" ? body.detail : `HTTP ${res.status}`,
          details: d?.details,
          request_id: d?.request_id,
        } as ApiError;
      } catch {
        // Ignorar si el cuerpo no es JSON.
      }
      throw new Error(error.message, { cause: error });
    }

    if (res.status === 204) {
      return undefined as T;
    }

    return res.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Tiempo de espera agotado al contactar al backend. Verifica que el servidor esté en ejecución.", { cause: err });
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

export const api = {
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    const response = await fetch(`${API_BASE}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      const detail = payload?.detail;
      throw new Error(typeof detail?.message === "string" ? detail.message : typeof detail === "string" ? detail : typeof payload?.message === "string" ? payload.message : "No fue posible iniciar sesión.");
    }
    return response.json() as Promise<{ access_token: string; token_type: string; expires_in: number }>;
  },
  me: () => request<{ id: string; email: string; is_admin: boolean }>(`${API_BASE}/auth/me`),
  get: <T>(path: string) => request<T>(`${API_BASE}${path}`),
  post: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>(`${API_BASE}${path}`, {
      method: "POST",
      body: body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined),
      headers: body instanceof FormData ? {} : { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      ...init,
    }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(`${API_BASE}${path}`, {
      method: "PATCH",
      body: body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined),
    }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(`${API_BASE}${path}`, {
      method: "PUT",
      body: body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined),
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
  getAnalysis: (analysisId: string) =>
    request<{
      analysis_id: string;
      page_id: string;
      estado: string;
      confianza_global: number | null;
      version_modelo: string | null;
      panels: Array<{ id: string; page_id: string; numero_orden: number; x: number; y: number; ancho: number; alto: number; confianza_deteccion: number | null }>;
      characters: Array<{ id: string; nombre: string; descripcion: string | null; confianza_identidad: number | null }>;
      appearances: Array<{ id: string; page_id: string; character_id: string; panel_id: string | null; confianza_deteccion: number | null }>;
      masks: Array<{ id: string; appearance_id: string; tipo_mascara: string; ruta_archivo: string; hash_sha256: string; ancho: number | null; alto: number | null }>;
    }>(`${API_BASE}/analysis/${analysisId}`),
  approveAnalysis: (analysisId: string) =>
    request<{ analysis_id: string; estado: string }>(`${API_BASE}/analysis/${analysisId}/approve`, {
      method: "POST",
    }),
  createColorization: (analysisId: string, modelId?: string) =>
    request<{ job_id: string; analysis_id: string; estado: string; progreso: number; mensaje: string | null; model_id?: string; version_modelo?: string }>(
      `${API_BASE}/colorizations?analysis_id=${encodeURIComponent(analysisId)}${modelId ? `&model_id=${encodeURIComponent(modelId)}` : ""}`,
      { method: "POST" }
    ),
  getColorization: (jobId: string) =>
    request<{ job_id: string; analysis_id: string; estado: string; progreso: number; mensaje: string | null; ruta_resultado: string | null; version_modelo: string | null }>(`${API_BASE}/colorizations/${jobId}`),
  downloadColorization: (jobId: string) => authenticatedBlob(`/colorizations/${jobId}/result`),
  listModels: (tarea?: string) => request<{ items: any[]; total: number }>(`${API_BASE}/models${tarea ? `?tarea=${encodeURIComponent(tarea)}&activo=true` : "?activo=true"}`),
  getAnalysisCharacters: (analysisId: string) => request<any>(`${API_BASE}/analysis/${analysisId}/characters`),
  groupAnalysisIdentities: (analysisId: string) => request<any>(`${API_BASE}/analysis/${analysisId}/group-identities`, { method: "POST" }),
  listCharacterAppearances: (characterId: string) => request<any>(`${API_BASE}/characters/${characterId}/appearances`),
  reviewIdentity: (appearanceId: string, characterId: string) => request<any>(`${API_BASE}/appearances/${appearanceId}/identity`, { method: "PATCH", body: JSON.stringify({ character_id: characterId }) }),
  addCharacterReference: (characterId: string, reference: string) => request<any>(`${API_BASE}/characters/${characterId}/reference`, { method: "PUT", body: JSON.stringify({ referencia_estable: reference }) }),
  getCharacterMemory: (characterId: string) => request<any>(`${API_BASE}/characters/${characterId}/memory`),
  updateCharacterMemory: (characterId: string, memory: Record<string, unknown>) => request<any>(`${API_BASE}/characters/${characterId}/memory`, { method: "PATCH", body: JSON.stringify(memory) }),
  updateCharacterAttribute: (characterId: string, name: string, value: string) => request<any>(`${API_BASE}/characters/${characterId}/attributes/${encodeURIComponent(name)}`, { method: "PATCH", body: JSON.stringify({ valor_sugerido: value }) }),
  approveCharacterAttribute: (characterId: string, name: string) => request<any>(`${API_BASE}/characters/${characterId}/attributes/${encodeURIComponent(name)}/approve`, { method: "POST" }),
  updateCharacterPalette: (characterId: string, name: string, hex: string) => request<any>(`${API_BASE}/characters/${characterId}/palettes/${encodeURIComponent(name)}`, { method: "PATCH", body: JSON.stringify({ valor_hex: hex }) }),
  approveCharacterPalette: (characterId: string, name: string) => request<any>(`${API_BASE}/characters/${characterId}/palettes/${encodeURIComponent(name)}/approve`, { method: "POST" }),
  getAnalysisMasks: (analysisId: string) => request<any[]>(`${API_BASE}/analysis/${analysisId}/masks`),
  downloadMask: (maskId: string) => authenticatedBlob(`/masks/${maskId}/content`),
  downloadPage: (pageId: string) => authenticatedBlob(`/pages/${pageId}/content`),
  correctMask: (appearanceId: string, corrections: Record<string, unknown>) => request<any>(`${API_BASE}/appearances/${appearanceId}/mask/correct`, { method: "PATCH", body: JSON.stringify({ correcciones: corrections }) }),
  replaceMask: (appearanceId: string, file: File) => { const body = new FormData(); body.append("file", file); return request<any>(`${API_BASE}/appearances/${appearanceId}/mask/replace`, { method: "PUT", body }); },
  editMask: (appearanceId: string, tipoMascara: string, file: File) => { const body = new FormData(); body.append("tipo_mascara", tipoMascara); body.append("file", file); return request<any>(`${API_BASE}/appearances/${appearanceId}/mask`, { method: "POST", body }); },
};

export async function authenticatedBlob(path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: authToken.get() ? { Authorization: `Bearer ${authToken.get()}` } : {},
  });
  if (response.status === 401 && authToken.get()) {
    authToken.clear();
    if (typeof window !== "undefined") window.dispatchEvent(new Event("sumi:unauthorized"));
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = payload?.detail;
    throw new Error(typeof detail?.message === "string" ? detail.message : typeof detail === "string" ? detail : typeof payload?.message === "string" ? payload.message : `HTTP ${response.status}`);
  }
  return response.blob();
}

