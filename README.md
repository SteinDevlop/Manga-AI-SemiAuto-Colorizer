<a id="readme-top"></a>

<div align="center">

# Manga AI SemiAuto Colorizer

**Aplicación local para colorización semiautomática de manga: detecta viñetas y personajes, configura paletas y máscaras, y ejecuta inferencia U-Net local con un checkpoint PyTorch registrado.**

[![FastAPI][FastAPI-badge]][FastAPI-url]
[![React][React-badge]][React-url]
[![TypeScript][TypeScript-badge]][TypeScript-url]
[![Vite][Vite-badge]][Vite-url]
[![PostgreSQL][PostgreSQL-badge]][PostgreSQL-url]
[![Redis][Redis-badge]][Redis-url]
[![Celery][Celery-badge]][Celery-url]
[![Pytest][Pytest-badge]][Pytest-url]
[![Docker][Docker-badge]][Docker-url]

[Qué es](#que-es) ·
[Inicio rápido](#inicio-rapido) ·
[Tu primera página](#tu-primera-pagina) ·
[Cómo funciona](#como-funciona) ·
[API](#api) ·
[Pruebas](#pruebas) ·
[Glosario](#glosario)

</div>

---

<a id="que-es"></a>
## Qué es

Manga AI SemiAuto Colorizer es una aplicación web local que colorea páginas de manga en blanco y negro de forma semiautomática. El usuario importa una imagen, el sistema detecta viñetas y personajes, agrupa apariciones por identidad, propone atributos cromáticos y presenta un editor para que el usuario confirme o corrija colores. Solo después de la aprobación se ejecuta la colorización.

El sistema cubre todo el recorrido:

1. **Carga y validación** de páginas de manga (imagen, hash SHA-256, metadatos).
2. **Detección de paneles** y de apariciones de personajes mediante adaptadores reemplazables.
3. **Agrupación de identidades** de personajes entre viñetas y páginas.
4. **Configuración cromática**: atributos (piel, cabello, ojos, vestimenta, accesorios) y paletas de color, con sugerencias automáticas editables.
5. **Gestión de máscaras**: creación, corrección y reemplazo de máscaras por personaje.
6. **Aprobación explícita** de la configuración antes de iniciar cualquier colorización.
7. **Trabajos de colorización** asíncronos con progreso, estados persistentes y descarga del resultado.

Todo el procesamiento pesado corre en workers independientes (CPU y GPU); la API nunca ejecuta inferencia dentro de una petición HTTP.

| Necesidad | Cómo la cubre el sistema |
|---|---|
| Colorizar páginas sin tocar el line art | Generación condicionada por máscaras y paletas aprobadas |
| Que el mismo personaje tenga el mismo color en todas las viñetas | Memoria de personaje con atributos estables y referencias persistentes |
| Que nadie pueda colorear sin aprobar | Bloqueo de trabajo de colorización hasta `APPROVED` |
| Que el trabajo pesado no bloquee la interfaz | Colas Celery + Redis; workers CPU y GPU independientes |
| Que los resultados no se pierdan al reiniciar | PostgreSQL para metadatos y estados; sistema de archivos para artefactos |

> [!NOTE]
> **Estado del proyecto.** Backend (FastAPI + SQLAlchemy + Alembic + Celery), frontend (React + TypeScript + Vite), autenticación JWT, Model Registry, workers, pruebas y Docker Compose están implementados. El motor de colorización disponible es U-Net local y requiere un checkpoint `.pt` compatible registrado. Los adaptadores mock permiten probar detección/análisis; los formatos ONNX y API aún no están conectados al worker U-Net.

### A quién está dirigido

| Rol | Qué hace con el sistema |
|---|---|
| Usuario final | Importa páginas, revisa personajes, elige colores y obtiene imágenes coloreadas |
| Desarrollador | Mantiene API, módulos, almacenamiento y despliegue |
| Ingeniero ML | Entrena, evalúa, versiona y sustituye modelos mediante adaptadores |
| Evaluador | Compara salidas mediante métricas y revisión humana |

<details>
<summary>¿Qué incluye hoy?</summary>

| Estado | Funcionalidad |
|---|---|
| Implementada | Estructura de repositorio monolito modular + workers |
| Implementada | Backend FastAPI con API `/api/v1`, casos de uso y repositorios |
| Implementada | PostgreSQL + SQLAlchemy 2 + Alembic para metadatos y estados |
| Implementada | Redis + Celery para cola de trabajos asíncronos |
| Implementada | Gestión de archivos y artefactos (hash SHA-256, nombres internos seguros) |
| Implementada | Modelos de dominio: Project, Page, Panel, Character, CharacterAppearance, CharacterAttribute, CharacterPalette, MaskArtifact, ColorizationJob, ModelManifest, CharacterMemory |
| Implementada | Estados de análisis y de trabajo con transiciones permitidas |
| Implementada | Adaptadores de IA mediante Protocolos (detección, segmentación, matching, colorización) |
| Implementada | Adaptadores mock para pruebas de flujo completo |
| Implementada | Frontend React + TypeScript + Vite con pantallas de proyectos, carga, análisis, editor, aprobación y colorización |
| Implementada | Pruebas backend (pytest) y frontend (Vitest) |
| Implementada | Docker Compose para PostgreSQL, Redis, API, workers y frontend |
| Implementada | CI/CD con GitHub Actions (CodeQL, OWASP Dependency-Check, ruff, mypy, pytest) |
| Implementada | Dependabot para dependencias Python y Node |

</details>

### Alcance y límites

- La aplicación se ejecuta localmente; no requiere servicios cloud en modo normal.
- No entrena modelos. Ejecuta inferencia con checkpoints U-Net `.pt` compatibles registrados; la inferencia ONNX/API es una integración posterior.
- No ejecuta inferencia pesada dentro de endpoints HTTP.
- No almacena imágenes binarias en PostgreSQL; solo metadatos y referencias a artefactos.
- Los casos de uso no están acoplados a una biblioteca o modelo de IA concreto.
- Las sugerencias automáticas de color son editables y marcan incertidumbre; no se inventan colores oficiales.
- No se inicia colorización si el análisis o la configuración requerida no está aprobado.

<details>
<summary>No está en alcance (fase posterior)</summary>

- Entrenamiento o ajuste fino de modelos generativos.
- Implementación de un editor profesional de ilustración raster/vectorial.
- Colaboración multiusuario o despliegue distribuido.
- Hacer scraping de manga o incorporar material protegido sin licencia.

</details>

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

---

<a id="inicio-rapido"></a>
## Inicio rápido

Esta guía lleva de un repositorio recién clonado a una instancia funcional. Tarda unos minutos si Docker ya está instalado.

### Prerrequisitos

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | 3.11+ | Backend |
| Docker y Docker Compose | Recientes | PostgreSQL, Redis, API, workers, frontend |
| Node.js | 20.19+ | Solo si vas a desarrollar el frontend |

### Instalación y arranque

```sh
# 1. Clonar
git clone https://github.com/SteinDevlop/Manga-AI-SemiAuto-Colorizer.git
cd Manga-AI-SemiAuto-Colorizer

# 2. Configuración e infraestructura
cp docker/.env.example docker/.env
# Edita docker/.env: define SECRET_KEY y, si usarás modelos API, ENCRYPTION_KEY.
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build

# 3. Crear el primer usuario administrador (se solicita contraseña de forma interactiva)
docker compose --env-file docker/.env -f docker/docker-compose.yml exec api \
  python -m app.cli create-user --email admin@example.com --admin
```

### Qué debería estar corriendo

| Servicio | Dirección | Uso |
|---|---|---|
| API (FastAPI) | `http://localhost:8000` | Backend REST |
| Swagger | `http://localhost:8000/api/v1/docs` | Referencia interactiva de la API |
| ReDoc | `http://localhost:8000/api/v1/redoc` | Referencia de lectura |
| Frontend (Vite) | `http://localhost:5173` | Interfaz de usuario |
| PostgreSQL | `localhost:5433` | Metadatos y estados; publicado solo en loopback |
| Redis | `localhost:6379` | Broker de Celery; publicado solo en loopback |

### Variables de entorno

Copia `docker/.env.example` a `docker/.env`. Ninguna variable es obligatoria en desarrollo; el ejemplo trae valores que funcionan en local.

| Variable | Valor de ejemplo | Para qué |
|---|---|---|
| `POSTGRES_USER` | `manga` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | `manga` | Contraseña de PostgreSQL |
| `POSTGRES_DB` | `manga_colorizer` | Base de datos principal |
| `DATABASE_URL` | `postgresql+asyncpg://manga:...@postgres:5432/manga_colorizer` | Cadena de conexión interna de los contenedores; desde el host usa `localhost:5433` |
| `REDIS_URL` | `redis://localhost:6379/0` | Broker de Celery y caché |
| `SECRET_KEY` | valor aleatorio de al menos 32 caracteres | Firma de tokens JWT |
| `ENCRYPTION_KEY` | clave Fernet generada | Cifrado de credenciales de modelos API |
| `STORAGE_ROOT` | `./data` | Directorio raíz para artefactos |

Nunca subas `.env` al repositorio ni pongas secretos reales en `.env.example`.

### Autenticación y primer acceso

La interfaz redirige a `/login` y protege las rutas de trabajo. No existe registro público. Crea el primer administrador con el comando anterior o configura `FIRST_ADMIN_EMAIL` y `FIRST_ADMIN_PASSWORD` antes del primer arranque. El token se conserva en `sessionStorage` durante la sesión del navegador y se envía como `Authorization: Bearer ...`; las descargas y vistas de resultados también se solicitan con ese encabezado.

Para crear usuarios adicionales, ejecuta el mismo comando `create-user` sin `--admin`.

### Docker Compose: operación

Ejecuta los comandos desde la raíz del repositorio. La ruta explícita al archivo Compose es necesaria porque vive en `docker/`.

```sh
# Arrancar o reconstruir imágenes
 docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build

# Ver estado y logs
 docker compose --env-file docker/.env -f docker/docker-compose.yml ps
 docker compose --env-file docker/.env -f docker/docker-compose.yml logs -f api worker-cpu

# Detener sin borrar datos
 docker compose --env-file docker/.env -f docker/docker-compose.yml stop

# Eliminar contenedores y red; conserva el volumen de PostgreSQL y bind mounts
 docker compose --env-file docker/.env -f docker/docker-compose.yml down

# Reiniciar servicios concretos
 docker compose --env-file docker/.env -f docker/docker-compose.yml restart api
 docker compose --env-file docker/.env -f docker/docker-compose.yml restart worker-cpu

# Solo en hosts NVIDIA con NVIDIA Container Toolkit instalado
 docker compose --profile gpu --env-file docker/.env -f docker/docker-compose.yml up -d --build

# BORRADO DESTRUCTIVO: elimina también el volumen persistente de PostgreSQL
 docker compose --env-file docker/.env -f docker/docker-compose.yml down -v
```

Los datos persistentes se guardan en el volumen `postgres_data` y en los directorios `docker/data/` y `docker/artifacts/`. El checkpoint de colorización debe estar registrado en Model Registry y ser un `.pt` compatible con el U-Net actual. Los modelos ONNX y API pueden registrarse y probarse, pero el worker U-Net de esta versión todavía no ejecuta esos formatos; la interfaz no los ofrece como modelos compatibles del pipeline.

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

---

<a id="tu-primera-pagina"></a>
## Tu primera página

El flujo básico tiene cuatro pasos. Las rutas están relativas a `http://localhost:8000/api/v1`.

**1. Crear un proyecto.**

```sh
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Mi manga", "descripcion": "Prueba de colorización"}'
```

Guarda el `id` del proyecto.

**2. Cargar una página.**

```sh
curl -X POST http://localhost:8000/api/v1/pages \
  -F "file=@pagina.jpg" \
  -F "project_id=tu-project-id"
```

La API responde `202 Accepted` con un `page_id`. La página queda en estado `uploaded`.

**3. Analizar la página.**

El sistema detecta paneles, personajes y agrupaciones automáticamente. Consulta el estado:

```sh
curl http://localhost:8000/api/v1/analysis/{page_id}
```

Cuando el análisis esté listo, verás personajes detectados con confianza y máscaras propuestas.

**4. Revisar y aprobar.**

Usa el frontend en `http://localhost:5173` para:
- Revisar personajes detectados y fusionar o separar identidades.
- Editar atributos (piel, cabello, ojos, vestimenta, accesorios) y paletas.
- Corregir máscaras si es necesario.
- Aprobar la configuración cromática.

Solo después de aprobar, puedes solicitar la colorización:

```sh
curl -X POST http://localhost:8000/api/v1/colorizations \
  -H "Content-Type: application/json" \
  -d '{"analysis_id": "tu-analysis-id"}'
```

La API responde `202 Accepted` con un `job_id`. Consulta el progreso hasta que el trabajo termine:

```sh
curl http://localhost:8000/api/v1/colorizations/{job_id}
```

Cuando el estado sea `completed`, descarga el resultado desde `ruta_resultado`.

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

---

<a id="como-funciona"></a>
## Cómo funciona

### El pipeline en una vista

Una página recorre las siguientes etapas. Cada etapa corre en su propia cola de Celery y se comunica con la siguiente mediante contratos de datos, no llamadas directas.

```mermaid
flowchart LR
    A[Usuario] -->|Carga página| B[API FastAPI]
    B -->|Guarda original + crea Page| FS[(Almacenamiento local)]
    B -->|Encola análisis| Q[(Redis / Cola)]
    Q -->|Tarea CPU| W[Worker CPU]
    W -->|Detecta paneles y personajes| W
    W -->|Guarda paneles, apariciones, máscaras| FS
    W -->|Guarda análisis en PostgreSQL| DB[(PostgreSQL)]
    W -->|Page = REVIEW_REQUIRED| DB
    B -->|Usuario revisa y aprueba| U[Usuario]
    U -->|Aprueba configuración| B
    B -->|Valida aprobación y crea job| Q
    Q -->|Tarea GPU| G[Worker GPU]
    G -->|Generación condicionada| IA[(Adaptadores de IA)]
    G -->|Guarda resultado| FS
    G -->|Job = COMPLETED| DB
    B -->|Muestra / descarga resultado| A
```

| Etapa | Cola | Recibe | Entrega | Estado |
|---|---|---|---|---|
| Análisis de página | `WORKER_CPU_QUEUES` | page_id | Paneles, apariciones, máscaras | `REVIEW_REQUIRED` |
| Aprobación humana | API | analysis_id | Estado `APPROVED` | `APPROVED` |
| Colorización | `WORKER_GPU_QUEUES` | analysis_id + configuración | Imagen coloreada | `COMPLETED` |

Dos precisiones:

- La **aprobación humana** es una transición de estado explícita y auditable. No se puede crear un trabajo de colorización sin aprobación válida.
- Los **adaptadores de IA** son reemplazables. En esta fase usan mocks; el adaptador real queda como integración pendiente.

### Flujo paso a paso

1. El usuario importa una imagen por la API o el frontend.
2. La API valida el archivo (MIME, tamaño, dimensiones), guarda el original en almacenamiento local y crea una `Page` en estado `uploaded`.
3. El worker CPU detecta paneles y personajes, guarda apariciones y máscaras, y crea un `Analysis` en estado `analysis_completed`.
4. El usuario revisa personajes, edita atributos y paletas, corrige máscaras si es necesario.
5. El usuario aprueba la configuración; la API marca el análisis como `APPROVED`.
6. El usuario solicita colorización; la API valida la aprobación y crea un `ColorizationJob`.
7. El worker GPU ejecuta la generación condicionada y guarda el resultado.
8. El frontend muestra el resultado y ofrece descarga.

### Arquitectura de bloques

```mermaid
flowchart TB
    subgraph Cliente["Cliente local"]
      FE[Frontend React + TypeScript]
    end

    subgraph Backend["Backend"]
      API[FastAPI]
      APP[Casos de uso / dominio]
      DB[(PostgreSQL)]
      REDIS[(Redis)]
      STORE[(Almacenamiento local)]
    end

    subgraph Workers["Procesamiento asíncrono"]
      CW[Worker CPU]
      GW[Worker GPU]
    end

    subgraph Engine["Motor de IA"]
      DET[Detection adapters]
      SEG[Segmentation adapters]
      ID[Identity matching]
      COND[Color conditioning]
      GEN[Generative models]
      REF[Refinement / upscaling]
    end

    FE <-->|REST + WebSocket| API
    API --> APP
    APP <--> DB
    APP <--> STORE
    APP --> REDIS
    REDIS --> CW
    REDIS --> GW
    CW <--> STORE
    GW <--> STORE
    GW --> DET
    GW --> SEG
    GW --> ID
    GW --> COND
    GW --> GEN
    GW --> REF
    DET --> SEG --> ID
    ID --> COND --> GEN --> REF
```

El sistema tiene cuatro capas: presentación (API y frontend), lógica de negocio (casos de uso y dominio), workers (procesamiento asíncrono) y motor de IA (adaptadores reemplazables).

### Módulos y responsabilidades

| Módulo | Responsabilidades | No debe hacer |
|---|---|---|
| `projects` | Crear, consultar y eliminar proyectos; organizar páginas | Ejecutar modelos |
| `assets` | Validar archivos, calcular hashes, administrar artefactos | Decidir colores |
| `page_analysis` | Orquestar análisis de página y paneles | Implementar internamente cada detector |
| `character_analysis` | Gestionar detecciones, apariciones y agrupación de identidades | Confirmar identidades sin intervención cuando hay ambigüedad |
| `character_configuration` | Administrar atributos, paletas y aprobación | Ejecutar inferencia generativa |
| `character_memory` | Persistir referencias, embeddings y atributos estables | Ser fuente de verdad para cambios de vestuario por escena |
| `colorization` | Validar precondiciones, crear trabajos y orquestar el pipeline | Acoplarse a una arquitectura concreta de modelo |
| `model_registry` | Registrar modelos, versiones, capacidades y disponibilidad | Descargar pesos arbitrarios sin validación |
| `jobs` | Estados, progreso, cancelación y reintentos | Guardar binarios grandes en PostgreSQL |
| `evaluation` | Métricas, resultados comparativos y feedback | Alterar resultados originales |

### Cómo se comunican los componentes

| Canal | Qué transporta |
|---|---|
| API REST (JSON) | Frontend ↔ backend, de forma síncrona |
| Celery + Redis | Tareas entre worker CPU y worker GPU |
| Caché Redis | Estado de cada trabajo (`job:{id}`) |
| Almacenamiento local | Imágenes originales, máscaras, previews y resultados |
| PostgreSQL | Metadatos y estados persistentes |

### Decisiones técnicas

| Decisión | Por qué |
|---|---|
| FastAPI | API REST con documentación automática (Swagger y ReDoc) |
| SQLAlchemy 2 async | ORM sobre PostgreSQL con pool asíncrono |
| Celery sobre Redis | Despacho asíncrono de tareas y caché de estado |
| Procesos CPU y GPU independientes | Separar tareas ligeras de inferencia pesada |
| Monolito modular + workers | Menor complejidad operativa; tipos y contratos compartidos |
| Motor de IA mediante Protocolos | Sustituir modelos sin cambiar casos de uso |
| Identificadores UUID | Identificadores estables y sin fugas de información |
| Fechas UTC ISO-8601 | Consistencia temporal en persistencia y API |
| Errores con `code` / `message` / `details` / `request_id` | Trazabilidad y depuración |

### Contratos y modelos de datos

Los contratos públicos están documentados en `docs/contratos/`:

| Contrato | Contenido |
|---|---|
| `identifiers.md` | Identificadores UUID para todas las entidades |
| `timestamps.md` | Fechas UTC en formato ISO-8601 |
| `api-versioning.md` | API versionada bajo `/api/v1` |
| `errors.md` | Errores con `code`, `message`, `details` y `request_id` |
| `artifacts.md` | Artefactos referenciados por `artifact_id`, nunca por rutas del cliente |
| `celery-tasks.md` | Tareas reciben IDs y parámetros serializables |
| `progress-events.md` | Eventos con `job_id`, `stage`, `progress`, `message`, `timestamp` |
| `dto-schemas.md` | Interfaces del motor de IA (Protocolos) |

No se comparten modelos ORM con el frontend ni con el motor de IA.

### Dónde está cada cosa

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── websocket/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── modules/
│   │   │   ├── projects/
│   │   │   ├── assets/
│   │   │   ├── page_analysis/
│   │   │   ├── character_analysis/
│   │   │   ├── character_configuration/
│   │   │   ├── character_memory/
│   │   │   ├── colorization/
│   │   │   ├── model_registry/
│   │   │   ├── jobs/
│   │   │   └── evaluation/
│   │   ├── application/
│   │   │   ├── use_cases/
│   │   │   ├── dto/
│   │   │   └── ports/
│   │   ├── infrastructure/
│   │   │   ├── database/
│   │   │   ├── repositories/
│   │   │   ├── storage/
│   │   │   └── queue/
│   │   └── workers/
│   │       ├── celery_app.py
│   │       └── tasks/
│   ├── alembic/
│   └── tests/
├── ai_engine/
│   ├── contracts/
│   ├── registry/
│   ├── detection/
│   ├── segmentation/
│   ├── identity/
│   ├── conditioning/
│   ├── colorization/
│   ├── refinement/
│   ├── evaluation/
│   └── adapters/
│       ├── mock/
│       └── real/
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.worker-cpu
│   └── Dockerfile.worker-gpu
├── data/
│   ├── originals/
│   ├── intermediates/
│   ├── masks/
│   ├── references/
│   ├── results/
│   └── manifests/
├── docs/
│   ├── arc42.md
│   ├── planes/
│   ├── architecture/
│   ├── adr/
│   └── contratos/
├── odd/
│   └── tasks/
├── tests/
└── .env.example
```

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

---

<a id="api"></a>
## API

### Endpoints principales

| Grupo | Endpoint | Descripción |
|---|---|---|
| Proyectos | `GET /api/v1/projects` | Listar proyectos |
| Proyectos | `POST /api/v1/projects` | Crear proyecto |
| Páginas | `POST /api/v1/pages` | Cargar y validar página |
| Páginas | `GET /api/v1/pages/{page_id}` | Obtener página por ID |
| Análisis | `GET /api/v1/analysis/{page_id}` | Obtener análisis con paneles, personajes y máscaras |
| Configuración | `PATCH /api/v1/characters/{id}/attributes/{name}` | Editar atributo de personaje |
| Configuración | `PATCH /api/v1/characters/{id}/palettes/{name}` | Editar entrada de paleta |
| Aprobación | `POST /api/v1/analysis/{id}/approve` | Marcar análisis como aprobado |
| Colorización | `POST /api/v1/colorizations` | Crear trabajo de colorización (solo si aprobado) |
| Trabajos | `GET /api/v1/colorizations/{job_id}` | Consultar estado y resultado del trabajo |
| Modelos | `GET /api/v1/models` | Listar modelos registrados |
| Modelos | `POST /api/v1/models` | Registrar nuevo modelo |

La referencia completa, con esquemas de entrada y salida, está en Swagger (`/api/v1/docs`) y ReDoc (`/api/v1/redoc`). Este README no repite cada endpoint.

### Formatos y errores

Las peticiones y respuestas son JSON.

| Código | Significado |
|---|---|
| `200` | Éxito |
| `202` | Trabajo aceptado; procesamiento en segundo plano |
| `400` | Solicitud inválida |
| `401` | No autenticado o sesión caducada |
| `403` | Autenticado, pero sin permiso para esa acción |
| `404` | Recurso no encontrado |
| `409` | Conflicto de estado (por ejemplo, colorización sin aprobación) |
| `500` | Error interno |

Los errores siguen el envelope `code` / `message` / `details` / `request_id`.

### Limitaciones de uso

- No almacenes credenciales ni secretos en el frontend.
- No asumas procesamiento síncrono; consulta el estado del trabajo por `job_id`.
- No inicies colorización si el análisis o la configuración requerida no está aprobado.

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

---

<a id="pruebas"></a>
## Pruebas y calidad

El backend usa **pytest**, configurado en `pyproject.toml`.

### Ejecutar las pruebas

```sh
cd backend
pytest                    # todas las pruebas
pytest tests/test_domain_models.py   # modelos de dominio
pytest tests/test_repositories.py    # repositorios
pytest tests/test_use_cases.py       # casos de uso
pytest tests/test_storage_service.py # servicio de almacenamiento
pytest tests/test_validators.py      # validadores de archivos
```

El backend pasa **144 pruebas**.

Para el frontend, desde `frontend/`:

```sh
npm test                 # pruebas Vitest
npm test -- --coverage   # cobertura
```

### Qué servicios necesita cada conjunto

| Pruebas | Necesitan |
|---|---|
| `tests/test_domain_models.py` | Ninguna (introspección de modelos) |
| `tests/test_repositories.py` | Ninguna (introspección de clases) |
| `tests/test_use_cases.py` | Ninguna (puertos Protocol) |
| `tests/test_storage_service.py` | Directorio temporal (isolado) |
| `tests/test_validators.py` | Ninguna (archivos temporales) |
| `tests/test_job_states.py` | Ninguna (máquina de estados) |
| `tests/test_progress_events.py` | Ninguna (eventos de progreso) |
| `tests/test_idempotency.py` | Ninguna (nombres de tareas y lógica) |
| `tests/test_reconciliation.py` | Ninguna (funciones de reconciliación) |

### Tipos de prueba

| Tipo | Qué verifica | Ejemplo |
|---|---|---|
| Modelo | Tablas, columnas, claves foráneas, índices | `test_domain_models.py` |
| Repositorio | Métodos CRUD, firma asíncrona | `test_repositories.py` |
| Caso de uso | Métodos `execute`, DTOs, errores P0 | `test_use_cases.py` |
| Almacenamiento | Guardar, leer, eliminar, existencia, ruta, hash | `test_storage_service.py` |
| Validador | MIME, tamaño, contenido vs extensión, nombre seguro | `test_validators.py` |
| Estados de trabajo | Transiciones válidas, estados terminales | `test_job_states.py` |
| Progreso | Campos `job_id`, `stage`, `progress`, `message`, `timestamp` | `test_progress_events.py` |
| Idempotencia | Nombres de tareas, guardado en estado terminal | `test_idempotency.py` |
| Reconciliación | Trabajos huérfanos, cancelación, transiciones | `test_reconciliation.py` |

### Datos de prueba

No se requieren datos externos; las pruebas usan estructuras en memoria y directorios temporales.

### Herramientas de calidad

- **Ruff**: lint y formato (`ruff check`, `ruff format --check`)
- **Mypy**: type-check (`mypy`)
- **Pytest**: pruebas unitarias y de integración

### Criterios para aceptar un cambio

- Las pruebas existentes siguen pasando.
- El cambio incluye pruebas del comportamiento nuevo.
- La cobertura no baja de forma significativa.
- El código pasa linting y formato.

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

---

<a id="glosario"></a>
## Glosario

| Término | Significado |
|---|---|
| Line art | Trazos y contornos originales del manga. |
| Panel / viñeta | Región individual de una página narrativa. |
| Character detection | Localización de una aparición de personaje. |
| Character identity matching | Estimación de qué apariciones corresponden al mismo personaje. |
| Character appearance | Una aparición concreta de un personaje en una viñeta. |
| Palette | Conjunto de colores definidos para atributos o regiones. |
| Mask | Imagen o mapa que delimita una región de interés. |
| Conditioning | Información que guía al modelo generativo. |
| Inference | Ejecución del modelo para producir una salida. |
| Worker | Proceso que ejecuta tareas asíncronas. |
| Artifact | Archivo producido o utilizado por una etapa del pipeline. |
| Job_id | Identificador de un trabajo de colorización; sirve para consultar su estado. |
| Human-in-the-loop | Intervención del usuario para validar o corregir decisiones de IA. |
| Baseline | Modelo o método inicial usado como referencia experimental. |
| Idempotencia | Repetir una operación produce el mismo resultado, sin duplicar datos. |

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

---

## Roadmap

- [x] P0 — Arquitectura, contratos y bootstrap
- [x] P1 — Backend, dominio y persistencia
- [x] P2 — Gestión de archivos y artefactos
- [x] P3 — Jobs, cola y workers
- [x] P4 — Análisis de página y visión por computador
- [x] P5 — Identidad y memoria de personajes
- [x] P6 — Configuración cromática, máscaras y aprobación
- [x] P7 — Frontend
- [x] P8 — Integración del motor de IA (sin modelo generativo real)
- [x] P9 — QA, integración, Docker y documentación final

Consulta las [issues abiertas](https://github.com/SteinDevlop/Manga-AI-SemiAuto-Colorizer/issues) para ver propuestas y problemas conocidos.

---

## Contribuciones

Toda contribución es bienvenida. Si tienes una sugerencia, haz un fork y envía un pull request, o abre un issue con la etiqueta `enhancement`.

1. Haz un fork del proyecto.
2. Crea tu rama (`git checkout -b feature/mi-funcionalidad`).
3. Confirma tus cambios (`git commit -m 'feat: añadir mi funcionalidad'`).
4. Sube la rama (`git push origin feature/mi-funcionalidad`).
5. Abre un pull request.

Los commits siguen [Conventional Commits](https://www.conventionalcommits.org/es/). No incluyas `Co-Authored-By` ni atribución de IA.

---

## Licencia

Copyright © 2026. Todos los derechos reservados.

Este software y su código fuente son propiedad de sus titulares. No se concede licencia para usar, copiar, modificar, distribuir, sublicenciar ni explotar comercialmente el software sin autorización previa y expresa por escrito. Que el repositorio sea público no concede derechos adicionales.

El texto completo está en `LICENSE`.

---

## Contacto

[@SteinDevlop](https://github.com/SteinDevlop)

<p align="right">(<a href="#readme-top">volver arriba</a>)</p>

[FastAPI-badge]: https://img.shields.io/badge/FastAPI-005571?logo=fastapi
[FastAPI-url]: https://fastapi.tiangolo.com/
[React-badge]: https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB
[React-url]: https://react.dev/
[TypeScript-badge]: https://img.shields.io/badge/TypeScript-3178C6?logo=typescript
[TypeScript-url]: https://www.typescriptlang.org/
[Vite-badge]: https://img.shields.io/badge/Vite-646CFF?logo=vite
[Vite-url]: https://vitejs.dev/
[PostgreSQL-badge]: https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white
[PostgreSQL-url]: https://www.postgresql.org/
[Redis-badge]: https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white
[Redis-url]: https://redis.io/
[Celery-badge]: https://img.shields.io/badge/Celery-37814A?logo=celery
[Celery-url]: https://docs.celeryq.dev/
[Pytest-badge]: https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest
[Pytest-url]: https://docs.pytest.org/
[Docker-badge]: https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
