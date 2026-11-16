# P6 — Configuración cromática, máscaras y aprobación

**Objetivo:** Implementar atributos de personaje (piel, cabello, ojos, vestimenta, accesorios), paletas de colores, máscaras de corrección, y flujo de aprobación explícita antes de colorizar.

**Rama:** feature/p5-identidad-memoria-personajes → feature/p6-configuracion-cromatica-mascaras-aprobacion (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend)

## Specs

S1: Atributos de personaje: piel, cabello, ojos, vestimenta, accesorios, con valores sugeridos (marcando incertidumbre) y aprobados. [docs/arc42.md:5.2; 8.6]
S2: Paletas de colores por personaje: color base, sombras, luces. [docs/arc42.md:5.2]
S3: Máscaras de corrección: editar o reemplazar máscaras generadas por IA. [docs/arc42.md:5.2; 8.2]
S4: Aprobación explícita: ninguna colorización inicia sin aprobación de identidades, atributos y paletas. [docs/arc42.md:ADR-005]
S5: Estados de análisis con aprobación (REVIEW_REQUIRED → EDITING → APPROVED). [docs/arc42.md:6.4]
S6: Errores reutilizan el envelope code/message/details/request_id de P0. [docs/contratos/errors.md]
S7: Pruebas de unidad para atributos, paletas, máscaras y aprobación (RED → GREEN). [docs/README.md:65]
S8: No inventar colores oficiales. Sugerencias automáticas editables y marcando incertidumbre. [docs/README.md:8]
S9: No iniciar colorización si el análisis/configuración requerida no está aprobado. [docs/README.md:9]

## Tasks

T1 — Modelos CharacterAttribute y CharacterPalette (ya existen de P1). Route: inline. Linked: S1, S2. Status: done.
T2 — Casos de uso de configuración cromática (editar atributos, paletas). Route: delegated (parallelism). Linked: S1, S2, S8. Status: done. Commit: 338386c.
T3 — Casos de uso de máscaras (editar, corregir, reemplazar). Route: delegated (parallelism). Linked: S3. Status: done. Commit: 338386c.
T4 — Flujo de aprobación (marcar análisis como APPROVED, bloquear colorización sin aprobación). Route: inline. Linked: S4, S5, S9. Status: done. Commit: 338386c.
T5 — Pruebas de unidad para configuración y aprobación. Route: inline. Linked: S7. Status: pending.

## Log

L1: "continua hasta el final" (usuario, 15-nov-2026) — ejecutar P3-P9 sin confirmación humana
L2: P6 completado: T2-T4 (9 casos de uso: cromática, máscaras, aprobación), T5 (22 pruebas). 131/131 suite backend pasando. Todos los specs S1-S9 cubiertos. (15-nov-2026)
