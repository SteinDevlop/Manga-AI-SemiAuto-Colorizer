# P2 — Gestión de archivos y artefactos

**Objetivo:** Implementar validación de archivos, cálculo de hashes, almacenamiento local de artefactos, servicio de almacenamiento y casos de uso para gestión de archivos (originales, máscaras, referencias, previews, resultados). No almacenar binarios en PostgreSQL.

**Rama:** feature/p1-backend-dominio-persistencia → feature/p2-gestion-archivos-artefactos (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend)

## Specs

S1: Servicio de almacenamiento local (backend/app/infrastructure/storage/service.py) con métodos: guardar archivo, leer archivo, eliminar archivo, existe, obtener ruta, calcular hash SHA-256. [docs/arc42.md:5.2; docs/arc42.md:8.2; docs/contratos/artifacts.md]
S2: Módulo de dominio `assets` con entidades/validadores: ArchivoValido (tipo MIME permitido, tamaño máximo, dimensiones máximas), validación de contenido real vs extensión, nombres internos seguros (sin path traversal). [docs/arc42.md:5.2; docs/arc42.md:8.1]
S3: Identificadores de artefacto (`artifact_id`) estables, nunca rutas arbitrarias proporcionadas por el cliente. [docs/planes/P0-arquitectura-bootstrap.md:46; docs/contratos/artifacts.md]
S4: Operaciones de archivo seguras e idempotentes (rehash antes de guardar, no sobrescribir accidentalmente, nombres generados internamente). [docs/README.md:68; docs/arc42.md:8.2]
S5: Casos de uso: subir archivo validado, obtener artefacto por artifact_id, listar artefactos de una página/trabajo, eliminar artefacto huérfano. [docs/arc42.md:5.2]
S6: Errores de dominio reutilizan el envelope `code/message/details/request_id` de P0. [docs/planes/P0-arquitectura-bootstrap.md:45; docs/contratos/errors.md]
S7: Pruebas de unidad para servicio de almacenamiento y validadores (RED → GREEN → refactor), usando almacenamiento aislado (directorio temporal). [docs/README.md:65; docs/arc42.md:10.5]
S8: No acoplar casos de uso a implementaciones de modelos de IA. [docs/README.md:7; docs/arc42.md:ADR-004]
S9: No ejecutar inferencia pesada dentro de endpoints HTTP (solo validación y almacenamiento). [docs/README.md:4; docs/arc42.md:2.1]

## Tasks

T1 — Servicio de almacenamiento local (guardar/leer/eliminar/existe/ruta/hash). Route: inline (foundation). Linked: S1, S3, S4. Status: done.
T2 — Validadores de archivo (MIME, tamaño, dimensiones, contenido real, nombre seguro). Route: delegated (parallelism, superficies disjuntas). Linked: S2, S4. Status: done.
T3 — Módulo de dominio assets (entidades de artefacto, repositorio de artefactos). Route: delegated (parallelism, superficies disjuntas). Linked: S2, S3, S5. Status: done.
T4 — Casos de uso de archivos (subir, obtener, listar, eliminar). Route: delegated (parallelism, superficies disjuntas). Linked: S5, S6. Status: done.
T5 — Pruebas de unidad para almacenamiento y validadores (RED → GREEN → refactor). Route: inline. Linked: S7. Status: done.

## Log

L1: "continua" (usuario, 15-nov-2026) — iniciar P2 gestión de archivos y artefactos
L2: P2 completado: T1 storage inline, T2-T4 delegadas en paralelo, T5 pruebas inline. 45/45 tests pasando (27 de P1 + 9 de P2 + 9 de storage/validators). Todos los specs S1-S9 cubiertos. (15-nov-2026)
