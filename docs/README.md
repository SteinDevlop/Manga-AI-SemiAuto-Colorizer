# Manga Colorizer — Paquete de planes multiagente

**Objetivo:** construir la aplicación web local completa, dejando el modelo generativo de colorización para una fase posterior.

## Alcance de esta entrega

Construir:
- Aplicación web local.
- API, persistencia y almacenamiento de imágenes.
- Cola de trabajos y workers.
- Análisis de páginas, paneles y personajes mediante adaptadores.
- Agrupación y revisión de identidades.
- Configuración de atributos, paletas y máscaras.
- Pipeline de colorización con contrato estable y adaptador mock.
- Historial, progreso, pruebas, Docker y documentación.

**Fuera de alcance:** entrenar, ajustar o implementar el modelo generativo final. El adaptador de colorización real debe quedar como integración pendiente; los mocks solo sirven para probar el flujo completo.

## Orden recomendado

1. P0 — Arquitectura, contratos y bootstrap.
2. P1 — Backend, dominio y persistencia.
3. P2 — Gestión de archivos y artefactos.
4. P3 — Jobs, cola y workers.
5. P4 — Análisis de página y visión por computador.
6. P5 — Identidad y memoria de personajes.
7. P6 — Configuración cromática, máscaras y aprobación.
8. P7 — Frontend.
9. P8 — Integración del motor de IA (sin modelo generativo real).
10. P9 — QA, integración, Docker y documentación final.

P1/P2/P3 pueden avanzar en paralelo después de P0, siempre que respeten los contratos. P4/P5 requieren P0 y los contratos de P1/P2. P6 requiere el modelo de dominio acordado en P0/P1. P7 puede iniciar con OpenAPI y fixtures/mock API aprobados. P8 define el seam de integración, no entrena el modelo. P9 acompaña todas las fases y cierra la integración.

## Reglas obligatorias para todos los agentes

1. Leer `../arquitectura_manga_colorizer_arc42.md` si está disponible en el repositorio; este paquete complementa ese documento.
2. No implementar ni entrenar el modelo generativo de colorización.
3. No introducir microservicios. Mantener monolito modular + procesos worker.
4. No ejecutar inferencia pesada dentro de endpoints HTTP.
5. No acceder directamente a tablas desde routers; usar casos de uso/repositorios.
6. No almacenar imágenes binarias en PostgreSQL. Guardar metadatos y referencias a artefactos.
7. No acoplar casos de uso a una biblioteca/modelo específico.
8. No inventar colores oficiales. Las sugerencias automáticas deben ser editables y marcar incertidumbre.
9. No iniciar colorización si el análisis/configuración requerida no está aprobado.
10. No realizar cambios fuera del alcance asignado sin aprobación del Tech Lead.
11. Mantener tipado, lint, pruebas y documentación actualizados.
12. No añadir secretos, pesos de modelos, datasets ni imágenes con licencias dudosas al repositorio.

## Convenciones sugeridas

- Backend: Python 3.11+ (confirmar versión exacta en P0), FastAPI, Pydantic, SQLAlchemy 2, Alembic.
- Cola: Celery + Redis.
- DB: PostgreSQL.
- Frontend: React + TypeScript + Vite.
- Pruebas backend: pytest.
- Pruebas frontend: Vitest + Testing Library; E2E con Playwright.
- Contratos API: OpenAPI generado desde FastAPI.
- Formato: Ruff/Black o Ruff formatter, mypy/pyright según decisión P0, ESLint/Prettier.
- Docker Compose para servicios locales.

Las versiones concretas deben fijarse en lockfiles y no dejar rangos abiertos en producción.

## Definition of Done global

- La funcionalidad tiene pruebas automatizadas.
- La documentación de uso y decisiones está actualizada.
- Los errores son explícitos y no se silencian.
- Las operaciones de archivos son seguras e idempotentes cuando corresponda.
- Los estados persistentes sobreviven a reinicios.
- No se ha añadido dependencia del modelo generativo futuro.
- El cambio pasa lint, type-check y tests relevantes.
- El contrato público y los eventos están documentados.
