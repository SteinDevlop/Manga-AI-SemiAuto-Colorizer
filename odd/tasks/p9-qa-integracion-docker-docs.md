# P9 — QA, integración, Docker y documentación final

**Objetivo:** Acompañar todas las fases con QA, cerrar la integración del pipeline completo, empaquetar con Docker Compose y producir documentación final de uso y decisiones.

**Rama:** feature/p8-integracion-motor-ia → feature/p9-qa-integracion-docker-docs (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend), Vitest (frontend)

## Specs

S1: Funcionalidad tiene pruebas automatizadas (backend + frontend). [docs/README.md:65]
S2: Documentación de uso y decisiones actualizada (ADR, contratos, README dev). [docs/README.md:66]
S3: Errores explícitos, no se silencian. [docs/README.md:67]
S4: Operaciones de archivos seguras e idempotentes. [docs/README.md:68]
S5: Estados persistentes sobreviven a reinicios. [docs/README.md:69]
S6: No se ha añadido dependencia del modelo generativo futuro. [docs/README.md:70]
S7: Cambio pasa lint, type-check y tests relevantes. [docs/README.md:71]
S8: Contrato público y eventos documentados. [docs/README.md:72]
S9: Docker Compose para servicios locales (PostgreSQL, Redis, API, workers CPU/GPU, frontend). [docs/README.md:60]

## Tasks

T1 — Integración end-to-end del pipeline completo (subida → análisis → configuración → aprobación → colorización → descarga). Route: inline. Linked: S1, S3, S5. Status: pending.
T2 — Docker Compose completo y verificación de arranque de todos los servicios. Route: inline. Linked: S9. Status: pending.
T3 — Lint, type-check y tests de todo el backend y frontend. Route: inline. Linked: S7. Status: pending.
T4 — Documentación final de uso y decisiones (README, ADR consolidados, contratos API). Route: inline. Linked: S2, S8. Status: pending.
T5 — Revisión final de Definition of Done global. Route: inline. Linked: S1-S9. Status: pending.

## Log

L1: "continua hasta el final" (usuario, 15-nov-2026) — ejecutar P3-P9 sin confirmación humana
