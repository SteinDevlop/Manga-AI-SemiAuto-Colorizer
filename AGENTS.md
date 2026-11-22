# AGENTS.md — Manga AI SemiAuto Colorizer

Instrucciones compactas para sesiones de OpenCode en este repositorio. Solo contiene lo que un agente probablemente no adivine por sí mismo; si no ayuda a evitar un error, no está aquí.

## Repo en una línea

Aplicación local de colorización semiautomática de manga: backend FastAPI + SQLAlchemy 2 + Alembic + Celery (PostgreSQL + Redis), workers CPU y GPU independientes del mismo monolito, frontend React + TypeScript + Vite, inferencia U-Net local con checkpoint `.pt` registrado. Los adaptadores de IA son reemplazables (mocks en pruebas).

## Comandos esenciales (ejecutar desde la raíz del repo)

### Infraestructura: Docker Compose

El compose vive en `docker/`, por eso siempre hace falta `-f` y `--env-file`:

```sh
cp docker/.env.example docker/.env   # editar SECRET_KEY si se usa
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build
docker compose --env-file docker/.env -f docker/docker-compose.yml logs -f api worker-cpu
docker compose --env-file docker/.env -f docker/docker-compose.yml down
```

Puertos publicados solo en loopback: API `127.0.0.1:8000`, frontend `127.0.0.1:5173`, PostgreSQL `127.0.0.1:5433` (contenedor `5432`), Redis `127.0.0.1:6379`.

### Backend local (sin Docker)

Existe `.venv` en la raíz. Todos los comandos backend corren desde `backend/` con `PYTHONPATH=backend`:

```sh
# API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Worker CPU
python -m celery -A app.workers.celery_app worker -Q WORKER_CPU_QUEUES -n cpu@localhost
```

Variables de entorno locales (ver `start_api.bat`, `start_worker.bat`, `start_local.ps1`; no se suben):

- `DATABASE_URL=postgresql+asyncpg://manga:manga_password@localhost:5433/manga_colorizer`
- `REDIS_URL=redis://localhost:6379/0`, `CELERY_QUEUES=WORKER_CPU_QUEUES`
- `STORAGE_ROOT=data`, `SUMI_COLORIZATION_CHECKPOINT=artifacts/checkpoints/sumi_unet_cpu_v1/best.pt`, `SUMI_COLORIZATION_RESULTS_DIR=artifacts/results`

### Migraciones

```sh
alembic -c alembic/alembic.ini upgrade head
```

El contenedor de la API lo ejecuta al arrancar (antes de uvicorn). `alembic/env.py` convierte `postgresql+asyncpg://` a `psycopg2` automáticamente.

### Backend: pruebas y calidad

```sh
cd backend
pytest                 # todas las pruebas; no necesitan servicios externos (memoria y directorios temporales)
ruff check
ruff format --check
mypy app               # CI usa: mypy app --explicit-package-bases --ignore-missing-imports
```

### Frontend

```sh
cd frontend
npm ci                 # instalar
npm run dev            # Vite en :5173, llama a http://localhost:8000/api/v1
npm test               # Vitest (jsdom, setup en src/__tests__/setup.ts)
npm run typecheck      # tsc --noEmit
npm run build          # vite build -> dist
```

E2E: Playwright en `frontend/tests/*.spec.ts` (requieren servicios levantados).

### Primer usuario administrador

```sh
docker compose --env-file docker/.env -f docker/docker-compose.yml exec api \
  python -m app.cli create-user --email admin@example.com --admin
```

o definir `FIRST_ADMIN_EMAIL` y `FIRST_ADMIN_PASSWORD` antes del primer arranque. Login: `POST /api/v1/auth/token` (JWT). Todo menos `/health` y `/api/v1/auth/*` requiere autenticación.

## Reglas críticas (hay pruebas que fallan si se ignoran)

1. **Dependencias Python:** `backend/tests/test_dependencies.py` exige que `backend/requirements.txt` y `backend/pyproject.toml` (`[project.dependencies]`) coincidan exactamente, que cada versión vaya con `==`, y que todo import de terceros en `app/` esté declarado (excepciones: `torch`, `onnxruntime`, `models` como opcionales; `starlette` vía `fastapi`). Si agregas una dependencia, edita **ambos** archivos con versiones fijas en el mismo cambio.
2. **ORM no compartido:** los modelos ORM del backend nunca se importan en frontend ni en `ai_engine/`; todo lo que cruza procesos son DTOs versionados en `docs/contratos/`.
3. **Aprobación previa:** no se crea un trabajo de colorización si el análisis no está `APPROVED` (`409`). La inferencia pesada nunca corre dentro de una petición HTTP; va por Celery a Redis.
4. **Git:** rama `main`; commits Conventional Commits (`feat(backend):`, `fix:`, `chore:`, `test:...`); **nunca** `Co-Authored-By` ni atribución de IA. CI en push/PR a `main` (`.github/workflows/ci.yml`): ruff, `ruff format --check`, mypy, pytest, tsc, vitest, `docker compose config`, CodeQL y Dependency-Check.

## Estructura que importa

- `backend/app/main.py` — entrada FastAPI (`uvicorn app.main:app`).
- `backend/app/workers/celery_app.py` — app de Celery; tareas en `backend/app/workers/tasks/`.
- `backend/app/api/routes/` — routers de la API (`/api/v1`).
- `backend/app/application/use_cases/` — lógica de negocio.
- `backend/app/modules/*` — dominios: `projects`, `assets`, `page_analysis`, `character_*`, `colorization`, `model_registry`, `jobs`, `evaluation`.
- `backend/alembic/versions/` — migraciones.
- `frontend/src` — React + Vite; puerto 5173.
- `docs/contratos/` — contratos entre procesos: identificadores UUID, timestamps UTC ISO-8601, errores (`code`/`message`/`details`/`request_id`), artefactos (`artifact_id`, nunca rutas del cliente), tareas Celery serializables, eventos de progreso.
- `odd/tasks/` — tareas de fase (p0..p9). Para trabajo rastreado tipo ODD, crear `odd/tasks/<feature>.md` siguiendo el formato de esos archivos.

## Gotchas operativos

- PostgreSQL se publica en `5433`, no en `5432`; desde los contenedores es `postgres:5432`.
- No se suben al repo: `.env`, `.venv`, `*.log`, `backend/data/`, `data/`, `docker/data/`, `ml/`, `model-creation/`, `artifacts/checkpoints/`, `start_api.bat`, `start_worker.bat`, `start_local.ps1`, `scripts/`. Ver `.gitignore`.
- Worker GPU: solo con `--profile gpu` y NVIDIA Container Toolkit/CUDA en el host; si no hay GPU, ejecutar el worker en el host contra el broker Redis local.
- Los adaptadores mock sirven para pruebas de flujo completo; el worker U-Net real requiere un checkpoint `.pt` compatible registrado en Model Registry.
