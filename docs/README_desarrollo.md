# Development README — Manga Colorizer (P0)

Manga Colorizer is a local web application for generative manga colorization. This document explains how to clone, install, run, and test the repository during P0 (architecture, contracts, and bootstrap).

## Repository structure

```
manga-colorizer/
├── backend/              # FastAPI backend (Python)
├── frontend/             # React + TypeScript frontend (Vite)
├── ai_engine/            # Decoupled AI engine (Python)
├── docker/               # Dockerfiles and compose-related files
├── docker-compose.yml    # Local multi-service orchestration
├── data/                 # Local storage: originals, intermediates, masks, results, manifests
├── datasets/             # Evaluation datasets (licensed)
├── experiments/          # ML experiments and benchmarks
├── docs/
│   ├── arc42.md          # Architecture reference
│   ├── architecture/     # Mermaid system diagrams
│   ├── adr/              # Architectural decision records
│   ├── contratos/        # DTOs and cross-process contracts
│   └── planes/           # Phase plans (P0..P9)
└── README_desarrollo.md  # This file
```

## Prerequisites

- Python 3.11+ (backend and AI engine)
- Node.js 20+ and npm (frontend)
- Docker and Docker Compose (optional, for PostgreSQL/Redis/local run)
- NVIDIA GPU with CUDA (optional, for GPU worker; CPU-only is supported)

## Environment

Copy the example file and fill in local values. `.env` is excluded from Git.

```bash
cp backend/.env.example backend/.env   # if present
cp frontend/.env.example frontend/.env # if present
```

Key variables (examples):

```text
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=5173
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=manga_colorizer
POSTGRES_USER=manga
POSTGRES_PASSWORD=manga
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
STORAGE_PATH=./data
MODELS_PATH=./data/manifests
LOG_LEVEL=INFO
```

## Quick start with Docker Compose

From the repository root:

```bash
docker-compose up -d
```

This starts PostgreSQL (5432), Redis (6379), FastAPI (8000), the frontend (5173), and the CPU worker. The GPU worker, if used, runs on the host or a CUDA container and connects to the local broker (see ADR-008 and arc42 §7.4).

Stop:

```bash
docker-compose down
```

## Running without Docker

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r pyproject.toml   # or pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API serves on `http://localhost:8000`. P0 provides placeholder endpoints; the contract surface is documented in `docs/contratos/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend serves on `http://localhost:5173` and calls the API at `http://localhost:8000/api/v1`.

### Workers

CPU worker:

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info -Q cpu
```

GPU worker (requires CUDA-capable environment):

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info -Q gpu --concurrency=1
```

## Running tests

### Backend (pytest)

```bash
cd backend
python -m pytest
```

P0 acceptance: CI runs at least one smoke test. Backend tests live in `backend/tests/`.

### Frontend (Vitest)

```bash
cd frontend
npm install
npm test        # or npm run test, per package.json scripts
```

Frontend tests live in `frontend/` and use Vitest.

## CI

The minimum CI pipeline (S8) runs:

1. Lint
2. Type-check
3. Tests (backend pytest, frontend Vitest)

CI configuration lives in `.github/workflows/` (to be added in P0). No repository-wide install or formatters are run outside CI.

## Ports

| Service | Port | Exposure |
|---------|------|----------|
| Frontend | 5173 | localhost only |
| FastAPI | 8000 | localhost only |
| PostgreSQL | 5432 | internal/local network |
| Redis | 6379 | internal/local network |
| Worker CPU | — | no public port |
| Worker GPU | — | no public port |

PostgreSQL and Redis are not required to be published to the host; in the default deployment they are reachable only through the application's private network (arc42 §7.2).

## Docs reference

- `docs/arc42.md` — full architecture reference
- `docs/architecture/` — Mermaid diagrams (context, blocks, sequences, states, deployment)
- `docs/adr/` — architectural decision records (ADR-001..ADR-015)
- `docs/contratos/` — DTOs and cross-process contracts
- `docs/planes/P0-arquitectura-bootstrap.md` — P0 plan and acceptance criteria

## P0 acceptance criteria (summary)

- A developer can clone and install dependencies following this README.
- Backend and frontend start with placeholder endpoints/screens.
- Entity, job, artifact, and error contracts are documented.
- P1–P8 agents can implement without inventing field names or states.
- CI runs at least one smoke test.
