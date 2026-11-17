# API Endpoints — Fase 1 (Rediseño de navegación y Model Registry)

Documenta los endpoints introducidos o modificados en la Fase 1 del plan de trabajo.
Prefijo base: `/api/v1`.

## Projects

### GET /api/v1/projects
Listado paginado de proyectos con filtros por estado y etapa.

Query params:
- `page` (int, ≥1, default 1)
- `size` (int, 1..100, default 20)
- `estado` (str, opcional): filtra por `status` del proyecto.
- `current_stage` (str, opcional): filtra por etapa actual.

Respuesta (lista):
- `id` (UUID string), `nombre`, `descripcion`, `tipo` (null), `portada` (URL de miniatura o null), `current_stage` (etapa actual: upload|analysis|character|mask|approve|colorize|export), `status` (en_progreso|completado|con_error|procesando), `progreso` (0..100), `created_at`, `updated_at`, `total`, `page`, `size`.

### GET /api/v1/projects/{project_id}
Detalle de proyecto con sus páginas y el análisis vigente.

Respuesta: campos de proyecto más `pages` (lista). Cada página incluye:
- `page_id` (UUID string): identificador de la página/subida.
- `analysis_id` (UUID string o null): el análisis **vigente** (más reciente creado para esa página). Si la página se vuelve a analizar, este campo apunta al nuevo análisis y el anterior queda en historial.
- `analysis_estado` (str o null): estado del análisis vigente.

### PATCH /api/v1/projects/{project_id}/stage
Transición de etapa con validaciones.

Body: `{ "action": "complete" | "regress", "stage": "<etapa>" }`.

Reglas de negocio (Fase 1, S8):
- No se puede completar una etapa sin haber completado las previas.
- `upload` no es retornable: una vez completada no se puede volver a completar ni retroceder a ella.
- Los retrocesos están permitidos desde `analysis` en adelante (character→analysis, mask→character, approve→mask, etc.) y solo a etapas ya completadas.
- Cuando todas las etapas están completadas, `status` pasa a `completado`.

Respuesta: `project_id`, `action`, `stage`, `current_stage`, `status`, `stage_progress`, `progreso`.

## Metrics

### GET /api/v1/metrics
Métricas agregadas para el dashboard.

Respuesta:
- `total_proyectos` (int)
- `proyectos_por_estado` (dict estado→count)
- `proyectos_por_etapa` (dict etapa→count)
- `jobs` (dict: total, activos, completados, fallidos)
- `ultimos_proyectos` (lista de los 5 proyectos más actualizados con id, nombre, current_stage, status, portada, updated_at).

## Model Registry

### GET /api/v1/models
Listado de manifiestos de modelo. Query params opcionales: `tarea`, `activo` (bool), `formato`.

### GET /api/v1/models/{model_id}
Detalle de un modelo. No expone claves de API cifradas.

### POST /api/v1/models
Registro de modelo.
- `source_type=local_file`: requiere `file` (.pt/.onnx), `nombre`, `familia`, `version`. Valida extensión, tamaño máximo y SHA-256; almacena en `artifact_type="models"` (fuera de la carpeta pública); verifica que el archivo carga mediante el adaptador antes de registrar. Queda activo por defecto (`is_active=true`).
- `source_type=api`: requiere `base_url` y credenciales. Llama a `health_check` del adaptador API **antes** de persistir; si falla, responde 409 y no guarda. La clave de API se cifra y solo se devuelve enmascarada.

### PATCH /api/v1/models/{model_id}/status
Activar (`disponible`) o desactivar (`deshabilitado`). Si hay jobs de colorización en ejecución vinculados al modelo, responde 409 y no desactiva (protección de uso en curso).

### PUT /api/v1/models/{model_id}
Editar nombre, descripción, parámetros y credenciales. Si cambia la clave de API, se regenera el cifrado.

### DELETE /api/v1/models/{model_id}
Eliminar modelo. Si hay jobs en ejecución, responde 409.

### POST /api/v1/models/{model_id}/test-connection
Prueba de conexión para modelos API (invoca `health_check` del adaptador). No persiste nada.

## Reglas de identificadores (defecto 0.9)

| Identificador | Representa | Se usa en |
|---|---|---|
| `page_id` | Página/imagen subida | Subida (`POST /api/v1/pages`), lanzar análisis (`POST /api/v1/analysis/{page_id}`), obtener análisis de una página (`GET /api/v1/analysis/{page_id}`) |
| `analysis_id` | Un análisis concreto generado para esa página | Aprobar (`POST /api/v1/analysis/{analysis_id}/approve`), crear colorización (`POST /api/v1/colorizations` con `analysis_id` en body) |

Una página puede tener varios análisis si se vuelve a ejecutar el análisis. El frontend debe usar siempre el `analysis_id` devuelto por `POST /api/v1/analysis/{page_id}` (o el `analysis_id` vigente en `GET /api/v1/projects/{project_id}`) en las rutas que esperan el ID del análisis, nunca reutilizar el `page_id`. Si una ruta que espera `analysis_id` recibe un `page_id`, el backend responde 404 con mensaje que indica el recurso no encontrado (ej. "analysis not found").

## Formato de errores

Todas las respuestas de error usan el envelope `{ code, message, details?, request_id? }` (ver `docs/contratos/errors.md`).
