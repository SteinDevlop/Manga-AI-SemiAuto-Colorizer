# Fase 1: Backend, modelo de proyecto y contratos de API

Header: objetivo = que el backend entregue lo que el nuevo frontend necesita y sea la fuente de verdad de las etapas del proyecto. branch = feature/plan-de-trabajo-fases. delivery strategy = ask-on-risk. test runner = pytest (backend) + vitest/tsc (frontend).

## Specs

S1 — Añadir/confirmar en el modelo de proyecto: `current_stage` (enum de las 7 etapas upload/analysis/character/mask/approve/colorize/export), `status` (en_progreso, completado, con_error, procesando), `stage_progress` (etapas completadas) y `cover_image` (referencia a la imagen subida). Citado del plan Fase 1.
S2 — Generar y almacenar una miniatura al subir la imagen, para usarla como portada de la tarjeta del proyecto. Citado del plan Fase 1.
S3 — Endpoint de listado de proyectos que devuelva por proyecto: id, nombre, tipo, portada (URL de miniatura), etapa actual, estado, porcentaje de avance y fecha de última actualización. Con paginación y filtro por estado. Citado del plan Fase 1.
S4 — Endpoint de detalle de proyecto con su etapa actual y las etapas completadas. Citado del plan Fase 1.
S5 — Identificadores (ver 0.9): el detalle del proyecto/página debe devolver `page_id` y el `analysis_id` vigente (último análisis válido). Si hay varios análisis, definir cuál es el vigente y exponer el historial. Citado del plan Fase 1.
S6 — Revisar que las respuestas de `POST /analysis/{page_id}` incluyan explícitamente el `analysis_id` creado, y que las rutas de aprobación y colorización documenten qué identificador esperan. Citado del plan Fase 1.
S7 — Mensaje de error distinguible: si una ruta que espera `analysis_id` recibe un `page_id`, el 404 debe indicar qué recurso no se encontró ("analysis not found"). Citado del plan Fase 1.
S8 — Endpoint de transición de etapa con validaciones: no avanzar sin completar la anterior; no volver a `upload` una vez completada; retrocesos permitidos desde `analysis` en adelante. Respuestas con errores claros. Citado del plan Fase 1.
S9 — Endpoint de subida con validación (tipo, tamaño máximo) y respuesta explícita de éxito/error. Citado del plan Fase 1.
S10 — Endpoint de métricas para el dashboard: total de proyectos, proyectos por estado, proyectos por etapa, jobs activos/fallidos/completados, últimos proyectos actualizados. Citado del plan Fase 1.
S11 — Verificar/ajustar endpoints para Results & Exports y Colorization Jobs (listado y estado). Citado del plan Fase 1.
S12 — Model Registry, modelo de datos: entidad `model` con id, nombre, versión, tarea, `source_type` (local_file | api), formato (pt | onnx | api, extensible), `is_active`, estado de salud (ok | error | no_verificado), metadatos y fechas. Citado del plan Fase 1.
S13 — Capa de adaptadores: interfaz común (validate, load, unload, infer, health_check) y un adaptador por tipo: PyTorch (.pt), ONNX (.onnx) y API externa. El pipeline consume modelos solo a través de esta interfaz. Citado del plan Fase 1.
S14 — Modelos locales: endpoint de subida de archivo con validación de extensión, tamaño máximo y checksum; almacenamiento fuera de la carpeta pública; verificación de que el archivo carga antes de registrarlo. Citado del plan Fase 1.
S15 — Seguridad de archivos .pt: cargar con `weights_only=True` o mecanismo equivalente/aislado, documentando el riesgo. Citado del plan Fase 1.
S16 — Modelos por API: registro con proveedor/nombre, URL base, autenticación, clave/token, modelo/endpoint y parámetros por defecto (timeout, reintentos). Endpoint de prueba de conexión antes de guardar. Citado del plan Fase 1.
S17 — Secretos: claves de API almacenadas cifradas, nunca devueltas al frontend (solo enmascadas) ni en logs. Citado del plan Fase 1.
S18 — Activar/desactivar: endpoints para activar y desactivar un modelo. Al registrar un modelo válido, queda activo por defecto. Varios modelos activos y uno predeterminado por tarea. Un modelo desactivado no debe poder ser seleccionado por el pipeline. Citado del plan Fase 1.
S19 — Protección de uso en curso: si un modelo tiene jobs en ejecución, impedir desactivarlo o eliminarlo (o avisar y exigir confirmación), sin dejar jobs huérfanos. Citado del plan Fase 1.
S20 — Endpoints de listado, detalle, edición (nombre, descripción, parámetros, credenciales) y eliminación de modelos. Citado del plan Fase 1.
S21 — Si no hay ningún modelo activo para una tarea requerida, el backend devuelve un error claro. Citado del plan Fase 1.
S22 — Migración de datos: asignar `current_stage` y `status` coherentes a proyectos ya existentes. Citado del plan Fase 1.
S23 — Documentar los contratos (OpenAPI o archivo equivalente). Citado del plan Fase 1.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S1, S22 | inline | pending | |
| T2 | S2 | inline | pending | |
| T3 | S3, S4 | inline | pending | |
| T4 | S5, S6, S7 | inline | pending | |
| T5 | S8 | inline | pending | |
| T6 | S9 | inline | pending | |
| T7 | S10 | inline | pending | |
| T8 | S11 | inline | pending | |
| T9 | S12, S13, S14, S15, S16, S17, S18, S19, S20, S21 | delegated (adaptadores + Model Registry HTTP son superficies nuevas disjuntas) | pending | |
| T10 | S23 | inline | pending | |

## Log

L1: Usuario solicitó ejecutar el plan de trabajo (frontend redesign + backend ajustes) sin supervisión humana, en local, sin Docker hasta Fase 10. Fase 0 completada (commit 2813844). Fase 1 en curso.
