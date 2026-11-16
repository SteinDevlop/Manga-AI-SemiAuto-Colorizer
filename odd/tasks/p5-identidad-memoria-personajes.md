# P5 — Identidad y memoria de personajes

**Objetivo:** Implementar memoria de personajes (embeddings, referencias estables), persistencia de identidades entre viñetas y páginas, y distinción entre atributos estables y por escena.

**Rama:** feature/p4-analisis-pagina-vision → feature/p5-identidad-memoria-personajes (crear antes del primer commit)
**Estrategia de entrega:** ask-on-risk (default)
**Runner de pruebas:** pytest (backend)

## Specs

S1: Tabla character_memory con embeddings y referencias estables por personaje. [docs/arc42.md:5.2; 8.5]
S2: Distinción entre atributos estables (cabello habitual, ojos) y atributos por escena (vestuario, accesorios). [docs/arc42.md:8.5]
S3: Un personaje puede cambiar de ropa sin convertirse en otra identidad. [docs/arc42.md:8.5]
S4: Referencias estables para reproducir consistencia cromática entre páginas. [docs/arc42.md:8.3; 8.5]
S5: Casos de uso: obtener memoria de personaje, actualizar atributos, agregar referencia, listar apariciones por identidad. [docs/arc42.md:5.2]
S6: Errores reutilizan el envelope code/message/details/request_id de P0. [docs/contratos/errors.md]
S7: Pruebas de unidad para memoria de personajes (RED → GREEN). [docs/README.md:65]

## Tasks

T1 — Modelo CharacterMemory y repositorio. Route: inline. Linked: S1, S2, S4. Status: done.
T2 — Casos de uso de memoria de personajes. Route: delegated (parallelism). Linked: S3, S5. Status: done.
T3 — Pruebas de unidad para memoria y casos de uso. Route: inline. Linked: S7. Status: done.

## Log

L1: "continua hasta el final" (usuario, 15-nov-2026) — ejecutar P3-P9 sin confirmación humana
L2: P5 completado: T1 (modelo CharacterMemory + repositorio + migración 0002), T2 (4 casos de uso de memoria), T3 (11 pruebas). 109/109 suite backend pasando. Todos los specs S1-S7 cubiertos. (15-nov-2026)
