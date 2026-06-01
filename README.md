# PrimeTradeAI Internship Assignment

FastAPI backend for user authentication, role-based access control, and task CRUD with PostgreSQL + Alembic.

## Features

- JWT authentication with login endpoint
- Password hashing with `passlib`
- Role-based access control for admin-only user management routes
- Versioned REST API under `/api/v1`
- PostgreSQL database with Alembic migrations
- Task CRUD scoped to authenticated user
- Swagger docs at `/docs`

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL
- PyJWT
- Passlib

## Project Structure

```text
backend/
  app/
    api/v1/         # Route handlers
    core/           # Config, JWT, dependencies
    db/             # Engine, sessions, DB init helpers
    models/         # SQLAlchemy models
    schemas/        # Pydantic request/response models
    services/       # Business logic
  migrations/       # Alembic env + revisions
  main.py           # FastAPI app entry
  seed.py           # Seed initial admin user
```

## Setup

### 1. Create env file

Create [backend/.env](/run/media/suyashk13/New%20Volume/Suyash/CodingPlatform/primetradeai_intern_task/backend/.env:1):

```env
SECRET_KEY=change_me
ACCESS_TOKEN_EXPIRE_MINUTES=30

POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=primetrade_db
POSTGRES_PORT=5432

BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
FIRST_SUPERUSER_EMAIL=admin@primetrade.ai
FIRST_SUPERUSER_PASSWORD=admin123
```

### 2. Install dependencies

```bash
uv sync
```

If `uv` not available:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Run migrations

From repo root:

```bash
alembic upgrade head
```

### 4. Seed admin user

```bash
cd backend
python seed.py
```

### 5. Start API server

```bash
cd backend
uvicorn main:app --reload
```

App runs at `http://127.0.0.1:8000`

## API Documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/api/v1/openapi.json`

## Authentication Flow

1. Register user with `POST /api/v1/users/`
2. Login with `POST /api/v1/login`
3. Send token in header:

```http
Authorization: Bearer <access_token>
```

Note: login endpoint uses OAuth2 form fields. Send email in `username` field.

## Main Endpoints

### Auth

- `POST /api/v1/login`

### Users

- `POST /api/v1/users/` - register
- `GET /api/v1/users/me` - current profile
- `PATCH /api/v1/users/me` - update current profile
- `DELETE /api/v1/users/me` - soft delete current account

### Admin User Management

- `GET /api/v1/users/`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}/role`
- `PATCH /api/v1/users/{user_id}/suspend`
- `DELETE /api/v1/users/{user_id}`

### Tasks

- `POST /api/v1/tasks/`
- `GET /api/v1/tasks/`
- `GET /api/v1/tasks/{task_id}`
- `PATCH /api/v1/tasks/{task_id}`
- `DELETE /api/v1/tasks/{task_id}`

## Database

Main tables:

- `users`
- `tasks`
- `alembic_version`

Migration files live in [backend/migrations](/run/media/suyashk13/New%20Volume/Suyash/CodingPlatform/primetradeai_intern_task/backend/migrations).

Create new migration:

```bash
alembic revision --autogenerate -m "message"
```

## Scalability Note

Current codebase uses layered structure:

- routes handle HTTP concerns
- services hold business logic
- schemas validate inputs/outputs
- models isolate persistence layer

This structure scales well for adding modules like notes, products, or teams without mixing concerns.

Next scalability steps:

1. Move auth, users, tasks into separate domain packages with explicit interfaces.
2. Add Redis for caching hot reads, rate limiting, and token/session support.
3. Add background workers for email, audit logs, and async jobs.
4. Add structured logging and monitoring for request tracing.
5. Put Postgres behind managed backups and connection pooling.
6. Scale app horizontally behind load balancer because API is stateless with JWT.
7. Split into microservices only after domain boundaries and traffic justify extra complexity.

## Demo Credentials

After running seed:

- Email: `admin@primetrade.ai`
- Password: `admin123`
