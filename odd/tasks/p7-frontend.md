# P7 — Frontend

**Objetivo:** Implementar la interfaz web local (React + TypeScript + Vite) con pantallas de proyectos, carga de páginas, editor de personajes y paletas, visor de progreso y descarga de resultados.

**Rama:** feature/p6-configuracion-cromatica-mascaras-aprobacion → feature/p7-frontend (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** Vitest + Testing Library (frontend)

## Specs

S1: Pantalla de inicio: lista de proyectos, crear nuevo proyecto, subir página. [docs/arc42.md:3.3; OBJ-01]
S2: Pantalla de análisis: mostrar paneles detectados, personajes agrupados, máscaras propuestas. [docs/arc42.md:3.3; OBJ-02]
S3: Editor de personajes: editar atributos (piel, cabello, ojos, vestimenta, accesorios), paletas de colores, sugerencias marcando incertidumbre. [docs/arc42.md:8.6; OBJ-03; S8 de P6]
S4: Flujo de aprobación: revisar y aprobar identidades, atributos y paletas antes de colorizar. [docs/arc42.md:ADR-005; S9 de P6]
S5: Pantalla de colorización: iniciar colorización (solo si aprobado), ver progreso por etapas, descargar resultado. [docs/arc42.md:6.3; OBJ-01]
S6: Pantalla de historial: ver trabajos anteriores, estados, métricas. [docs/arc42.md:8.3]
S7: Contratos API: consumir endpoints /api/v1 definidos en P0 (docs/contratos/). [docs/planes/P0-arquitectura-bootstrap.md:44]
S8: Pruebas frontend: Vitest + Testing Library para componentes críticos. [docs/README.md:56]
S9: UI copy en inglés, sin estilo de persona (sin slang, sin CAPS, sin exclamaciones). [docs/README.md:49-61]

## Tasks

T1 — Estructura frontend y componentes base (layout, navegación, API client). Route: inline. Linked: S1, S7. Status: done.
T2 — Pantalla de proyectos y carga de página. Route: delegated (parallelism). Linked: S1. Status: in-progress.
T3 — Pantalla de análisis y editor de personajes/paletas. Route: delegated (parallelism). Linked: S2, S3. Status: in-progress.
T4 — Flujo de aprobación y pantalla de colorización/progreso. Route: delegated (parallelism). Linked: S4, S5. Status: done.
T5 — Pantalla de historial y descarga. Route: inline. Linked: S6. Status: done.
T6 — Pruebas frontend (Vitest + Testing Library). Route: inline. Linked: S8. Status: done.

## Log

L1: "continua hasta el final" (usuario, 15-nov-2026) — ejecutar P3-P9 sin confirmación humana
L2: P7 completado: T1-T6 (estructura base, 7 pantallas, rutas, 9 archivos de prueba Vitest). App.tsx registrado con todas las rutas. types/index.ts extendido con Panel, Appearance, Mask. tsx no ejecutado (node_modules ausente, install prohibido). Próximo: P8 (integración motor IA sin modelo real).
