# Mars Agent Guide

## Purpose

Mars is the **Pythonista** variant of Mercury: a small FastAPI backend boilerplate centered on JWT auth, PostgreSQL persistence, Redis initialization, and optional Google OIDC login. SQLAlchemy models and **Alembic** own the database schema (not Flyway SQL files).

This file is a working analysis for future agents so they can navigate the repository quickly and avoid common mistakes.

**Current release line:** latest tag is `v0.1.3` (Alembic migrations, `solar.manifest.yaml`, Solar Stack scaffold support).

## Stack Summary

| Layer | Choice |
|-------|--------|
| API | FastAPI `0.128.0` (`fastapi[standard]`) |
| Server | Uvicorn (via `src/app.py`) |
| ORM | SQLAlchemy **2.0** (`DeclarativeBase`, `sessionmaker`) |
| Validation | Pydantic **v2** (`ConfigDict`, `model_dump`) |
| Database | PostgreSQL 16 (Docker), driver `psycopg2-binary` |
| Cache | Redis 7 (initialized at startup; not used in route logic yet) |
| Auth | JWT (`python-jose`) + OAuth2 password flow + Google OIDC |
| Passwords | Passlib (`sha256_crypt` when `JWT_ALGORITHM=HS256`, else `bcrypt`) |
| Migrations | Alembic 1.13+ (`alembic/versions/`, autogenerate from models) |
| Tests | `unittest` (unit), `pytest` + `TestClient` (integration) |
| Tooling | Docker Compose, Ruff, Bandit, Renovate, GitHub Actions |

## Repository Shape

Top-level areas:

| Path | Role |
|------|------|
| `src/app.py` | **Uvicorn entrypoint** (`python src/app.py` in Docker); loads `main:app` |
| `src/main.py` | **FastAPI application** — `app` object, CORS, `create_all`, Redis init, routers |
| `src/restful_ressources.py` | Central router mounting under `/{API_VERSION}` |
| `src/routes/` | HTTP route definitions (thin; delegate to controllers) |
| `src/controllers/` | Request logic and DB mutation/query logic |
| `src/models/` | SQLAlchemy models (`User` only) |
| `src/schemas/` | Pydantic request/response schemas |
| `src/database/` | PostgreSQL engine/session (`postgres_db.py`), Redis bootstrap (`redis_db.py`) |
| `src/middleware/auth_guard.py` | JWT decoding and auth dependencies |
| `src/utils/` | Password hashing, JWT, OIDC helpers, response filtering, env parsing |
| `alembic/` | Alembic migrations (`initial_schema`, `seed_admin_user`, …) |
| `src/integration_tests/` | API-level tests |
| `src/unit_tests/` | Minimal direct-function coverage |
| `ci/` | Shell wrappers for Docker-based lint/test/security |
| `.github/workflows/` | CI: test, lint, scan, build, release-on-tag |

Do not confuse `app.py` and `main.py`: Docker and local runs start **`src/app.py`**; the ASGI app lives in **`src/main.py`**.

## Runtime Flow

1. `src/app.py` starts Uvicorn with `main:app`, host/port/workers from environment.
2. Importing `main` triggers side effects in `src/main.py`:
   - `Base.metadata.create_all(bind=dbEngine)` — creates tables if missing
   - `redis.init()` — global Redis client
   - FastAPI app construction and router registration
3. `constants/environment_variables.py` validates required env vars **at import time** (raises `RuntimeError` if missing).
4. Routes delegate to controllers; controllers use `get_db()` sessions.
5. Protected routes use JWT dependencies in `middleware/auth_guard.py`.

**Implication:** importing the app is not side-effect free. PostgreSQL and Redis must be reachable for a normal boot. Prefer Docker Compose for full-stack validation.

## API Surface

Mounted under `/{API_VERSION}` (default `v1`):

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| `GET` | `/health` | — | `{"alive": true, "status": "ok"}` |
| `POST` | `/token` | — | OAuth2 password grant; `username` = email **or** username |
| `POST` | `/user/register` | — | Email/password registration |
| `POST` | `/user/login` | — | JSON login; returns user + nested `token` object |
| `GET` | `/user` | Bearer | Current user |
| `PATCH` | `/user` | Bearer | Update current user |
| `GET` | `/oidc/google/login` | — | Google authorization URL |
| `GET` | `/oidc/google` | — | OAuth `code` or `credential` → JWT |
| `GET` | `/oidc/google/token` | — | Decode provided JWT |
| `GET` | `/admin/user/all` | Admin | List users (passwords stripped) |
| `GET` | `/admin/user/{user_id}` | Admin | Single user |
| `POST` | `/admin/user/register` | Admin | Create user |
| `PATCH` | `/admin/user/{user_id}` | Admin | Update user |
| `DELETE` | `/admin/user/{user_id}` | Admin | Delete user (204) |

Swagger UI is at `/` (`docs_url="/"`).

## Data Model

Single application model: `User` (`public.user` table).

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK, `uuid_generate_v4()` |
| `username` | string | optional |
| `email` | string | unique |
| `password` | string | nullable (OIDC-only users) |
| `is_admin` | bool | |
| `disabled` | bool | |
| `oidc_configs` | JSONB | provider mappings array |

Google OIDC users are created with `password=None`.

## Alembic Migrations

Revisions live in `alembic/versions/`:

| Revision | Purpose |
|----------|---------|
| `initial_schema` | `uuid-ossp` extension + `user` table (from SQLAlchemy model) |
| `seed_admin_user` | Dev admin `test@admin.com` / `Cloud.456` (sha256_crypt hash) |

Compose service `mars_migrate` runs `alembic upgrade head` before `mars_api`.

Autogenerate workflow: update models → `alembic revision --autogenerate -m "description"` → review → `alembic upgrade head`.

## Auth Model

Two login paths:

- **`POST /token`**: OAuth2 form; `username` accepts email or username; returns `{ access_token, token_type }`; failures → **401**
- **`POST /user/login`**: JSON email + password; returns `{ id, email, token: { ... } }`; failures → **404** (via `authenticate_user`)

JWT payload uses `sub` = user **email**. User resolution always re-queries by email.

Dependencies:

- `get_current_user` — valid JWT + user exists
- `get_current_active_user` — not `disabled` (400 if inactive)
- `get_current_admin_user` — `is_admin` (400 if not admin); **does not** check `disabled`

Default seeded admin (README): `test@admin.com` / `Cloud.456`.

## Environment Model

Required at import (`validate_required_env()`):

`LISTEN_ADDR`, `LISTEN_PORT`, `APP_VERSION`, `APP_TITLE`, `APP_DESCRIPTION`, `API_VERSION`, `POSTGRES_*` (db, user, password, port, host), `JWT_SECRET_KEY`, `JWT_ALGORITHM`.

Commonly set but not validated as required:

`APP_ENV`, `API_URL`, `REDIS_HOST`, `REDIS_PORT`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `HTTP_REQUEST_TIMEOUT`, Google OIDC vars.

`OIDC_GOOGLE_REDIRECT_URI` is derived: `{API_URL}/{API_VERSION}/oidc/google`.

Baseline: copy `.env.dist` → `.env`. Docker Compose loads `.env` for all services.

Pool tuning (optional): `POSTGRES_SIZE_POOL`, `POSTGRES_MAX_OVERFLOW`, `POSTGRES_POOL_TIMEOUT`, `POSTGRES_POOL_RECYCLE` (defaults in `postgres_db.py`).

Uvicorn tuning (optional): `UVICORN_WORKERS`, `UVICORN_TIMEOUT_KEEP_ALIVE`, `UVICORN_TIMEOUT_GRACEFUL_SHUTDOWN`.

## Docker and CI

Compose services:

| Service | Role |
|---------|------|
| `mars_api` | API (non-root `app` user, healthcheck on `/v1/health`) |
| `mars_db` | PostgreSQL 16 |
| `mars_cache` | Redis 7 |
| `mars_migrate` | Alembic (`alembic upgrade head`) |
| `mars_integration_tests` | `pytest -v` |
| `mars_unit_tests` | `unittest discover` |
| `mars_linter` | `ruff check` |
| `mars_security` | `bandit` |

Commands:

```bash
docker compose up --build --force-recreate          # full stack
./ci/unit-test.sh
./ci/integration-test.sh
./ci/lint.sh
./ci/security.sh
```

GitHub Actions (`main` / `develop` / PRs):

- **test.yml** — unit + integration via `ci/*.sh`
- **lint.yml** — Ruff
- **scan.yml** — Bandit
- **build.yml** — Docker image `ayoub3bidi/mars:latest` on `main`
- **release.yml** — GitHub Release on push of tag matching `v*`

Renovate (`renovate.json`) groups pip minor/patch with automerge; majors and core frameworks (FastAPI, SQLAlchemy, Pydantic) need manual review.

## Test Reality

Coverage is shallow but integration tests improved since v0.3.1:

- **Unit:** single health test (`routes.health`); runs from `src/` in Docker.
- **Integration:** health + admin CRUD flow; `admin_headers` fixture logs in via `/token`; `_ensure_admin_user_exists()` makes tests resilient if seed migration order differs.
- Tests import the real app (`main:app`) — need DB, Redis, migrations, and full `.env`.

Local non-Docker runs need `PYTHONPATH=src` and installed deps from `requirements.txt`.

## Release History (Mars)

Mars was forked from Mercury with Alembic replacing Flyway. Notable stack choices:

- **SQLAlchemy 2.0** + **Pydantic v2**
- **Alembic** migrations in `alembic/versions/` (autogenerate from models)
- Compose service `mars_migrate` runs `alembic upgrade head` before `mars_api`
- **`solar.manifest.yaml`** at repo root for [sun](https://github.com/ayoub3bidi/sun) scaffolds

## Architectural Strengths

- Small, traceable codebase with consistent route → controller layout.
- Alembic revisions tied to SQLAlchemy models; readable seed for local dev.
- Full Docker dev loop (migrate → api → tests).
- Auth, admin, and OIDC scaffolding ready to extend.
- CI covers test, lint, security, build, and tag releases.
- SQLAlchemy 2 + Pydantic v2 align with current ecosystem defaults.

## Main Risks and Sharp Edges

1. **Startup side effects** — `create_all()` + Redis init on `main` import complicates testing and duplicates Alembic.
2. **Dual schema management** — Alembic is source of truth for production; `create_all()` can drift or mask migration gaps.
3. **Inconsistent auth responses** — `/token` (401) vs `/user/login` (404); different response shapes.
4. **Admin GET by id** — `remove_password_from_user(user)` when `user is None` → **500** instead of 404.
5. **Password scheme tied to JWT algorithm** — `sha256_crypt` iff `HS256`; should be independent config.
6. **Admin auth** — `get_current_admin_user` does not enforce `disabled`.
7. **Redis** — connected but unused in business logic (bootstrap only).
8. **Response filters** — `utils/filter.py` mutates ORM `__dict__` in place; risky if objects are reused.
9. **Seeded admin** — fine for dev; must be removed/changed in production.

## Recommendations For Future Agents

- Prefer **Docker Compose** for anything that imports `src/main.py`.
- Treat **Alembic** as the schema source of truth; consider removing `create_all()` in a follow-up.
- Preserve route/controller/module layout.
- Keep JWT `sub=email` unless refactoring all auth paths together.
- Add tests for auth failures, OIDC edge cases, and admin 404 paths — current coverage will not catch regressions.
- When adding migrations: update models → `alembic revision --autogenerate -m "description"` → review → `alembic upgrade head`.
- Inspect git state before large edits; `main` may be ahead of latest tag.

## Suggested Improvement Order

1. Remove `create_all()` from startup; rely on Alembic only.
2. Normalize auth status codes and response shapes across `/token` and `/user/login`.
3. Guard `GET /admin/user/{id}` for missing users (404 before filter).
4. Decouple password hashing from `JWT_ALGORITHM`.
5. Enforce `disabled` on admin dependencies (or document intentional bypass).
6. Use Redis for sessions/rate-limit/cache when extending the boilerplate.
7. Expand integration tests (user login, register, negative auth, OIDC mocks).

## Local Validation (analysis run)

Succeeded:

- Source inventory and architecture review
- `python3 -m compileall -q src`
- `python3 -m ruff check src` — all checks passed

Not run in this shell (use Docker instead):

- Unit/integration tests (need Compose stack and `.env`)
- Bandit security scan

## Release Tagging

Tags in this repo use a **`v` prefix** (`v0.1.3`, not `0.1.3`). Pushing `v*` triggers `.github/workflows/release.yml` to create a GitHub Release with generated notes.
