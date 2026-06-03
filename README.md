# Finance Report

Sistema de clasificacion y analisis de gastos personales que procesa extractos bancarios Excel (.xlsx), clasifica transacciones mediante un motor hibrido (reglas + ML), y presenta dashboards con analisis financiero detallado. Incluye asistente financiero con IA, deteccion de malos habitos, y traduccion colaborativa de comercios.

## Stack tecnologico

| Capa | Tecnologia | Version |
|------|-----------|---------|
| **Backend** | Python + FastAPI | 3.12+ |
| **Frontend** | TypeScript + Next.js 14 (App Router) | 5.x |
| **ORM** | SQLAlchemy 2.0 + Alembic | latest |
| **Base de datos** | PostgreSQL 16 (Supabase) | 16 |
| **Cache** | Redis 7 (Upstash) | 7 |
| **Mensajeria** | RabbitMQ | 3.13 |
| **LLM** | Google Gemini 1.5 Flash | latest |
| **ML** | scikit-learn + sentence-transformers | latest |
| **Graficos** | Recharts + Tremor | latest |
| **Contenedores** | Docker + Docker Compose | latest |
| **Orquestacion** | Kubernetes (Oracle OKE) | — |
| **CI/CD** | GitHub Actions | — |
| **Observabilidad** | OpenTelemetry + Grafana Cloud | — |

## Requisitos previos

- **Docker Desktop** (con Docker Compose)
- **Python 3.12+** (para desarrollo local sin Docker)
- **Node.js 20+** (para desarrollo local del frontend)
- **Poetry** (gestor de dependencias Python)

## Como levantar en desarrollo

### Con Docker Compose (recomendado)

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Levantar todos los servicios (10 contenedores)
docker compose up -d

# 3. Ver logs
docker compose logs -f backend

# 4. Detener servicios
docker compose down
```

Servicios disponibles:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### Sin Docker (desarrollo local)

#### Backend

```bash
cd src/backend

# Instalar dependencias
poetry install

# Ejecutar migraciones (requiere PostgreSQL corriendo)
poetry run alembic upgrade head

# Sembrar datos iniciales (categorias predefinidas)
python scripts/seed_data.py

# Iniciar servidor de desarrollo con hot-reload
poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd src/frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo con hot-reload
npm run dev
```

## Estructura del proyecto

```
finance-report/
├── .github/workflows/              # CI/CD pipelines
│   ├── ci.yml                      # Lint + test (backend + frontend)
│   ├── deploy-backend.yml          # Deploy a Oracle OKE
│   └── deploy-frontend.yml         # Deploy a Vercel
├── docs/
│   ├── architecture.md             # ADRs, diagramas C4, stack, contratos API
│   ├── analysis/                   # Requerimientos, modelo de dominio
│   └── features/                   # Features y tareas
├── k8s/                           # Manifiestos Kubernetes (Oracle OKE)
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml               # Template con placeholders
│   ├── deployment-backend.yaml
│   ├── deployment-workers.yaml
│   ├── service-backend.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
├── src/
│   ├── backend/                    # FastAPI (Python)
│   │   ├── pyproject.toml          # Poetry: dependencias, scripts, config
│   │   ├── Dockerfile              # Multi-stage (dev + prod)
│   │   ├── alembic.ini             # Migraciones BD
│   │   ├── alembic/
│   │   ├── src/
│   │   │   ├── domain/             # Entidades, value objects, eventos, repositorios
│   │   │   ├── application/        # CQRS: commands, queries, handlers, DTOs
│   │   │   ├── infrastructure/     # ORM, RabbitMQ, Redis, R2, Gemini
│   │   │   ├── api/                # FastAPI routers, middleware, schemas
│   │   │   └── workers/            # ExtractProc, ClassSvc, NotifSvc
│   │   ├── tests/
│   │   └── scripts/
│   └── frontend/                   # Next.js (TypeScript)
│       ├── package.json
│       ├── Dockerfile
│       ├── src/
│       │   ├── app/                # App Router (pages + layouts)
│       │   ├── components/         # Dashboard, transacciones, UI
│       │   ├── hooks/              # useApi, useAuth
│       │   ├── lib/                # api client, auth, utils
│       │   └── types/              # TypeScript interfaces
│       └── tests/
├── docker-compose.yml              # 10 contenedores para desarrollo local
├── .env.example                    # Variables de entorno requeridas
└── README.md
```

## Arquitectura (Clean Architecture + DDD)

El backend sigue Clean Architecture con separacion en 4 capas:

```
api/ (presentacion)
  ↓ depende de
application/ (casos de uso CQRS)
  ↓ depende de
domain/ (entidades, value objects, eventos)
  ↑ implementa
infrastructure/ (ORM, RabbitMQ, Redis, R2, Gemini)
```

**10 contenedores** definidos en `docker-compose.yml`:
1. Web App SPA (Next.js)
2. API Backend (FastAPI)
3. PostgreSQL
4. Redis
5. RabbitMQ
6. Procesador de Extractos (worker)
7. Servicio de Clasificacion (worker)
8. Servicio de IA / Chat (integrado en FastAPI)
9. Servicio de Notificaciones (worker)
10. Almacenamiento (MinIO / R2)

## Comandos utiles

### Backend

```bash
cd src/backend

poetry run pytest                          # Ejecutar tests
poetry run pytest --cov=src                # Tests con cobertura
poetry run ruff check src/ tests/          # Lint
poetry run mypy src/                       # Type check
poetry run alembic revision --autogenerate -m "descripcion"  # Nueva migracion
poetry run alembic upgrade head            # Aplicar migraciones
python scripts/seed_data.py                # Sembrar datos iniciales
```

### Frontend

```bash
cd src/frontend

npm run dev              # Servidor de desarrollo
npm run build            # Build de produccion
npm run lint             # ESLint
npm run type-check       # TypeScript check
npm run test             # Ejecutar tests
npm run test:coverage    # Tests con cobertura
```

### Docker

```bash
docker compose up -d                        # Iniciar todo
docker compose up backend -d                # Solo backend
docker compose logs -f backend              # Logs del backend
docker compose exec backend bash            # Shell en el contenedor
docker compose down -v                      # Detener y eliminar volumenes
```

## Licencia

MIT
