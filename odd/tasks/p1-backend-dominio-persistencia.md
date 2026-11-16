# P1 — Backend, dominio y persistencia

**Objetivo:** Implementar entidades de dominio, repositorios, casos de uso base y migraciones iniciales para proyectos, páginas, paneles, personajes, atributos, paletas, máscaras, análisis y trabajos de colorización.

**Rama:** feature/p0-bootstrap → feature/p1-backend-dominio-persistencia (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend)

## Specs

S1: Base SQLAlchemy 2 declarativa y sesión tipada; configuración de conexión desde `backend/app/core/config.py` (DATABASE_URL). [docs/arc42.md:5.2; docs/planes/P0-arquitectura-bootstrap.md:22]
S2: Entidades de dominio: Project, Page, Panel, Character, CharacterAppearance, CharacterAttribute, CharacterPalette, MaskArtifact, Analysis, ColorizationJob, ModelManifest. [docs/planes/P0-arquitectura-bootstrap.md:22-33; docs/arc42.md:5.2]
S3: Relaciones entre entidades (Project tiene Pages, Page tiene Panels y Analysis, Character tiene Appearances, Appearance pertenece a Page y Character, MaskArtifact referencia Appearance/Page, ColorizationJob referencia Analysis/Page). [docs/arc42.md:5.2; docs/contratos/identifiers.md]
S4: Identificadores UUID para todas las entidades; fechas UTC ISO-8601 en persistencia. [docs/planes/P0-arquitectura-bootstrap.md:42-43; docs/contratos/identifiers.md; docs/contratos/timestamps.md]
S5: Migración Alembic inicial que crea todas las tablas de las entidades S2. [docs/planes/P0-arquitectura-bootstrap.md:34]
S6: Repositorios por entidad con métodos CRUD base (get, list, create, update, delete, exists). [docs/arc42.md:5.2]
S7: Casos de uso base: crear proyecto, crear página, obtener proyecto por ID, listar páginas de proyecto. [docs/arc42.md:5.2]
S8: Errores de dominio reutilizan el envelope `code/message/details/request_id` de P0. [docs/planes/P0-arquitectura-bootstrap.md:45; docs/contratos/errors.md]
S9: Pruebas de unidad para repositorios y casos de uso base (RED → GREEN). [docs/README.md:65; docs/planes/P0-arquitectura-bootstrap.md:67]
S10: No acoplar casos de uso a implementaciones de modelos de IA; los casos de uso dependen de puertos/interfaces. [docs/README.md:7; docs/arc42.md:ADR-004]

## Tasks

T1 — Base de datos y sesión SQLAlchemy + configuración Alembic. Route: inline (foundation). Linked: S1, S4. Status: done. Commit: 7d8c7be.
T2 — Entidades de dominio (modelos SQLAlchemy), un archivo por entidad. Route: delegated (parallelism, superficies disjuntas). Linked: S2, S3, S4. Status: done. Commit: c7e1c2c.
T3 — Migración Alembic inicial (crea tablas de S2). Route: inline (depende de T2). Linked: S5. Status: done. Commit: 7d8c7be.
T4 — Repositorios por entidad (CRUD base). Route: delegated (parallelism, superficies disjuntas). Linked: S6. Status: done. Commit: 93260ef.
T5 — Casos de uso base (proyecto, página). Route: delegated (parallelism, superficies disjuntas). Linked: S7, S8. Status: done. Commit: d53c986.
T6 — Pruebas de unidad para repositorios y casos de uso. Route: inline (RED → GREEN → refactor). Linked: S9. Status: done. Commit: 2dddb94.

## Log

L1: "Hazlo" (usuario, 15-nov-2026) — iniciar P1 backend, dominio y persistencia
L2: P1 completado: 5 work-unit commits (7d8c7be T1-T3, 93260ef T4, d53c986 T5, c7e1c2c T2, 2dddb94 T6). 27/27 pruebas pasando. Todos los specs S1-S10 cubiertos. (15-nov-2026)
