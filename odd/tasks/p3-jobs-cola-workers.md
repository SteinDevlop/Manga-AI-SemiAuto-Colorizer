# P3 — Jobs, cola y workers

**Objetivo:** Implementar estados de trabajos, cola Celery con Redis, workers CPU y GPU, reintentos idempotentes, progreso y recuperación de tareas fallidas.

**Rama:** feature/p2-gestion-archivos-artefactos → feature/p3-jobs-cola-workers (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend)

## Specs

S1: Estados de trabajos (pending, preprocessing, colorizing, refining, completed, failed, cancelled) con transiciones persistentes. [docs/arc42.md:6.4]
S2: Tareas Celery reciben IDs y parámetros serializables, nunca objetos ORM ni binarios. [docs/planes/P0-arquitectura-bootstrap.md:47]
S3: Eventos de progreso con job_id, stage, progress, message, timestamp. [docs/planes/P0-arquitectura-bootstrap.md:48]
S4: Worker CPU: hashes, normalización, paneles, operaciones auxiliares (sin GPU). [docs/arc42.md:6.1]
S5: Worker GPU: detección, segmentación e inferencia pesada, concurrencia controlada (1), modelo residente. [docs/arc42.md:6.1; ADR-006]
S6: Reintentos idempotentes: reintentar una tarea no debe duplicar artefactos ni corromper estado. [docs/arc42.md:ADR-002]
S7: Cola y DB no quedan desincronizadas: estados persistentes, reconciliación de tareas intermedias. [docs/arc42.md:11]
S8: Worker GPU limita concurrencia y registra VRAM, duración, resolución, modelo por ejecución. [docs/arc42.md:6.5]
S9: Pruebas de unidad para estados, eventos de progreso y reintentos idempotentes. [docs/README.md:65]

## Tasks

T1 — Modelo ColorizationJob y estados (extender de P1). Route: inline. Linked: S1. Status: done. Commit: c8f70f5.
T2 — Configuración Celery (app, broker Redis, backend, serialización JSON, UTC). Route: inline. Linked: S2, S3. Status: done. Commit: c8f70f5.
T3 — Tareas Celery: analyze_page (CPU), colorize_page (GPU), con reintentos y progreso. Route: delegated (parallelism). Linked: S2, S3, S6. Status: done. Commit: 77646aa.
T4 — Worker CPU y worker GPU. Route: delegated (parallelism). Linked: S4, S5, S8. Status: done. Commit: 8f444d1.
T5 — Reconciliación y recuperación. Route: inline. Linked: S7. Status: done. Commit: 2e6f30d.
T6 — Pruebas de unidad. Route: inline. Linked: S9. Status: done. Commit: pending.

## Log

L1: "Si, puedes dejar de pedir confirmacion humana , continua hasta el final" (usuario, 15-nov-2026) — continuar P3-P9 sin confirmación
L2: P3 completado: 5 work-unit commits + pruebas. 21/21 tests P3, 66/66 suite backend. Todos los specs S1-S9 cubiertos. (15-nov-2026)
