# P0 — Arquitectura, contratos y bootstrap

**Objetivo:** Establecer la base del repositorio, las decisiones técnicas y los contratos que permitirán trabajar en paralelo sin conflictos.

**Rama:** main → feature/p0-bootstrap (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend), Vitest (frontend)

## Specs

S1: Estructura inicial del monorepo con directorios backend/, frontend/, ai_engine/, docker/, docs/. [docs/planes/P0-arquitectura-bootstrap.md:14-19; docs/arc42.md:5.3]
S2: Configuración por entorno mediante .env.example y settings tipados. [docs/planes/P0-arquitectura-bootstrap.md:20]
S3: Convenciones de nombres, imports, errores, logging y versionado de API. [docs/planes/P0-arquitectura-bootstrap.md:21]
S4: Entidades y relaciones iniciales: Project, Page, Panel, Character, CharacterAppearance, CharacterAttribute, CharacterPalette, MaskArtifact, Analysis, ColorizationJob, ModelManifest. [docs/planes/P0-arquitectura-bootstrap.md:22-33; docs/arc42.md:5.2]
S5: DTO/contratos entre backend, workers y AI Engine. [docs/planes/P0-arquitectura-bootstrap.md:34; docs/arc42.md:5.4]
S6: Estados y transiciones permitidas. [docs/planes/P0-arquitectura-bootstrap.md:35; docs/arc42.md:6.4]
S7: ADR para decisiones que aún no estén cerradas. [docs/planes/P0-arquitectura-bootstrap.md:36; docs/arc42.md:9]
S8: Pipeline CI mínimo: lint, type-check y tests. [docs/planes/P0-arquitectura-bootstrap.md:37]
S9: README de desarrollo. [docs/planes/P0-arquitectura-bootstrap.md:38]
S10: docs/architecture/ con diagramas Mermaid. [docs/planes/P0-arquitectura-bootstrap.md:54]

## Tasks

T1 — Backend bootstrap: estructura backend/, pyproject.toml, FastAPI app base, settings, configuración. Route: delegated (parallelism). Linked: S1-S3, S5. Status: done. Commit: b11b07f.
T2 — Frontend bootstrap: estructura frontend/, package.json, Vite, React + TypeScript, pantalla placeholder. Route: delegated (parallelism). Linked: S1, S3. Status: done. Commit: b11b07f.
T3 — Infra/Docker bootstrap: docker/, docker-compose.yml, Dockerfiles. Route: delegated (parallelism). Linked: S2. Status: done. Commit: b11b07f.
T4 — Documentación y contratos: docs/architecture/ Mermaid, ADR, DTO/contratos, README de desarrollo. Route: delegated (parallelism). Linked: S4-S10. Status: done. Commit: b11b07f.

## Log

L1: "Entonces inicia el plan de trabajo y delega en múltiples agentes para maximizar resultados" (usuario, 15-nov-2026)
L2: P0 completado: 4 writers en paralelo (backend, frontend, infra/docker, docs/contratos), commit b11b07f en feature/p0-bootstrap. Todos los specs S1-S10 cubiertos. Docker compose config validado. (15-nov-2026)
