/** Tipos compartidos del frontend (DTOs que reflejan los contratos de backend P0/P1/P2). */

export type Project = {
  id: string;
  nombre: string;
  descripcion?: string;
  created_at: string;
  updated_at: string;
};

export type Page = {
  id: string;
  project_id: string;
  nombre_archivo_original: string;
  hash_sha256: string;
  ruta_archivo: string;
  mime_type?: string;
  ancho?: number;
  alto?: number;
  tamano_bytes?: number;
  estado: string;
  created_at: string;
  updated_at: string;
};

export type Analysis = {
  id: string;
  page_id: string;
  estado: string;
  confianza_global?: number;
  version_modelo?: string;
  created_at: string;
  updated_at: string;
};

export type Character = {
  id: string;
  nombre: string;
  descripcion?: string;
  confianza_identidad?: number;
  created_at: string;
  updated_at: string;
};

export type CharacterAttribute = {
  id: string;
  character_id: string;
  nombre_atributo: string;
  valor_sugerido?: string;
  valor_aprobado?: string;
  esta_aprobado: boolean;
  confianza_sugerencia?: number;
};

export type CharacterPalette = {
  id: string;
  character_id: string;
  nombre_color: string;
  valor_hex?: string;
  esta_aprobado: boolean;
};

export type Panel = {
  id: string;
  page_id: string;
  numero_orden: number;
  x: number;
  y: number;
  ancho: number;
  alto: number;
  confianza_deteccion?: number;
};

export type Appearance = {
  id: string;
  page_id: string;
  character_id: string;
  panel_id?: string;
  confianza_deteccion?: number;
};

export type Mask = {
  id: string;
  appearance_id: string;
  tipo_mascara: string;
  ruta_archivo: string;
  hash_sha256: string;
  ancho?: number;
  alto?: number;
  version: number;
};

export type MaskArtifact = {
  id: string;
  appearance_id: string;
  tipo_mascara: string;
  ruta_archivo: string;
  hash_sha256: string;
  ancho?: number;
  alto?: number;
  version: number;
};

export type ColorizationJob = {
  id: string;
  analysis_id: string;
  estado: string;
  progreso: number;
  mensaje?: string;
  ruta_resultado?: string;
  version_modelo?: string;
  created_at: string;
  updated_at: string;
};

export type ApiError = {
  code: string;
  message: string;
  details?: Record<string, any>;
  request_id?: string;
};
