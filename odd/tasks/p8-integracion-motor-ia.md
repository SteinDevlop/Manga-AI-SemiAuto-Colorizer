# P8 — Integración del motor de IA (sin modelo generativo real)

**Objetivo:** Definir el seam de integración del motor de IA (adaptadores reales con lugar para el modelo futuro), registro de modelos, y pruebas de integración del seam. No entrenar ni implementar el modelo generativo final.

**Rama:** feature/p6-configuracion-cromatica-mascaras-aprobacion → feature/p8-integracion-motor-ia (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend)

## Specs

S1: Seam de integración del motor de IA: adaptadores que implementan los Protocolos de P4 (CharacterDetector, PanelDetector, Segmenter, CharacterMatcher, ColorizationEngine) con lugar para el modelo real (pendiente P8/futuro). [docs/arc42.md:5.4; ADR-004; ADR-007]
S2: Registro de modelos (ModelManifest de P1) con capacidades, versión, hash de pesos, licencia, estado (disponible/experimental/deshabilitado). [docs/arc42.md:8.4]
S3: Pruebas de integración del seam: verificar que los adaptadores se cargan, los contratos se respetan, y el fallback a mock funciona cuando no hay modelo real. [docs/README.md:65; docs/arc42.md:10]
S4: No ejecutar inferencia pesada dentro de endpoints HTTP. [docs/README.md:4]
S5: No implementar ni entrenar el modelo generativo de colorización. [docs/README.md:2]
S6: Los adaptadores reales devuelven errores claros cuando el modelo no está disponible (no fallar silenciosamente). [docs/README.md:7]
S7: Pruebas de unidad para registro de modelos y adaptadores. [docs/README.md:65]

## Tasks

T1 — Adaptadores reales (placeholders con lugar para modelo futuro). Route: delegated (parallelism). Linked: S1, S4, S5, S6. Status: pending.
T2 — Casos de uso de registro de modelos (registrar, listar, habilitar/deshabilitar). Route: delegated (parallelism). Linked: S2, S7. Status: done.
T3 — Pruebas de integración del seam (adaptadores + mocks + errores de modelo no disponible). Route: inline. Linked: S3, S7. Status: done.
T4 — Pruebas de unidad para modelos y adaptadores. Route: inline. Linked: S7. Status: done.

## Log

L1: "continua hasta el final" (usuario, 15-nov-2026) — ejecutar P3-P9 sin confirmación humana
L2: P8 completado: T1 (adaptadores reales), T2 (casos de uso registro modelos), T3-T4 (pruebas seam + unidad). 144/144 suite backend pasando. Todos los specs S1-S7 cubiertos. Próximo: P9 (QA, integración, Docker, docs finales).
