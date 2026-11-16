# P4 — Análisis de página y visión por computador

**Objetivo:** Implementar detección de paneles, detección y agrupación de personajes, extracción de máscaras, mediante adaptadores reemplazables (sin implementar el modelo generativo de colorización).

**Rama:** feature/p3-jobs-cola-workers → feature/p4-analisis-pagina-vision (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend)

## Specs

S1: Contratos de adaptadores de detección (CharacterDetector, Segmenter, CharacterMatcher) como Protocols, sin acoplar a biblioteca/modelo específico. [docs/arc42.md:5.4; ADR-004; ADR-007]
S2: Detección de paneles: localizar regiones de viñeta en una página, con confianza y bounding box. [docs/arc42.md:3.3; 5.2]
S3: Detección de personajes: localizar apariciones de personaje en paneles/página, con confianza. [docs/arc42.md:3.3; 5.2]
S4: Agrupación de identidades: estimar qué apariciones corresponden al mismo personaje, con confianza de matching. [docs/arc42.md:3.3; 8.5]
S5: Extracción de máscaras: delimitar regiones de personaje/fondo, almacenadas como MaskArtifact. [docs/arc42.md:3.3; 8.2]
S6: Los adaptadores son mocks/stubs en esta fase (modelo real es integración pendiente P8). [docs/README.md:17]
S7: Pruebas de unidad para adaptadores y casos de uso de análisis (RED → GREEN). [docs/README.md:65]
S8: No ejecutar inferencia pesada dentro de endpoints HTTP. [docs/README.md:4]

## Tasks

T1 — Protocols de adaptadores (detección, segmentación, matching). Route: inline. Linked: S1. Status: done. Commit: 6dfb14c.
T2 — Casos de uso de análisis de página. Route: delegated (parallelism). Linked: S2, S3, S5. Status: done. Commit: ce042fd.
T3 — Adaptadores mock para paneles, personajes, máscaras. Route: delegated (parallelism). Linked: S2, S3, S5, S6. Status: done. Commit: 3793a65.
T4 — Casos de uso de agrupación de identidades. Route: delegated (parallelism). Linked: S4. Status: done. Commit: 6598062.
T5 — Pruebas de unidad para adaptadores y casos de uso. Route: inline. Linked: S7. Status: done. Commit: pending.

## Log

L1: "continua hasta el final" (usuario, 15-nov-2026) — ejecutar P3-P9 sin confirmación humana
L2: P4 completado: 5 work-unit commits + pruebas. 98/98 suite backend pasando. Todos los specs S1-S7 cubiertos. (15-nov-2026)
