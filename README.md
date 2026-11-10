# Mars
<p align="center">
    <img src="./src/assets/mars.png"/> <br/>
    Pythonista backend boilerplate. Alembic migrations, SQLAlchemy-native schema
</p>

<p align="center">
    <img src="https://img.shields.io/badge/Made%20with-Python-1f425f.svg">
    <img src="https://img.shields.io/github/release/ayoub3bidi/mars">
</p>

> **Solar Stack** — scaffold a customized copy with one command: see the [ecosystem map](https://github.com/ayoub3bidi/sun/blob/v1.0.0/docs/SOLAR_STACK.md)

## Table of content

* [Introduction](#Introduction)
* [Docker Hub image](#docker-hub-image)
* [Setup](#setup)
* [Test the API](#test-the-api)
* [Test the database](#test-the-database)
* [How to add database migrations](#how-to-add-database-migrations)
* [Integration and Unit Testing](#integration-and-unit-testing)
* [Linter](#linter)
* [Security Scan](#security-scan)

## Introduction

Mars is the **Pythonista** variant of [Mercury](https://github.com/ayoub3bidi/mercury): same FastAPI stack, but schema is owned by **Alembic** and SQLAlchemy models instead of Flyway SQL files.

This project uses:
- Basic [OAuth2](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/?h=jwt) authentication, utilizing the FastAPI security module. It also supports user authentication via Google integration.
- [PostgreSQL](https://hub.docker.com/_/postgres) as its main database, [Redis](https://hub.docker.com/_/redis) for cache and task broker storage, and [Alembic](https://alembic.sqlalchemy.org/) for database migrations.
- Optional Celery worker and LangGraph agent services, with a local OpenAI-compatible mock endpoint.
- Liveness/readiness checks, request IDs, JSON request logs, Prometheus metrics, and opt-in OpenTelemetry traces.
- Unit and integration tests.
- Security scanner (Bandit).

## Docker Hub image

A pre-built API image is published to Docker Hub and GHCR on each push to `main`:

- **Repository:** [ayoub3bidi/mars](https://hub.docker.com/r/ayoub3bidi/mars)
- **GHCR:** `ghcr.io/ayoub3bidi/mars`

GitHub Actions publishes with the repository `GITHUB_TOKEN` and the `DOCKER_HUB_USERNAME` / `DOCKER_HUB_ACCESS_TOKEN` secrets. GitLab main-branch publishing also requires `GHCR_USERNAME` and `GHCR_TOKEN` CI variables.

```shell
docker pull ayoub3bidi/mars:latest
```

Use it alongside your own Postgres and Redis setup, or clone this repo and run the full stack with `docker compose` (see [Setup](#setup)).

### Project architecture

```
├── alembic
│   └── versions
├── src
│ └── assets
│ └── constants
│ └── controllers
│     ├── admin
│     ├── user
│ └── database
│     ├── postgres_db.py
│     ├── redis_db.py
│ └── integration_tests
│ └── middleware
│     ├── auth_guard.py
│ └── models
│ └── routes
│     ├── admin
│     ├── user
│ └── schemas
│ └── unit_tests
│ └── utils
│ └── app.py
│ └── main.py
│ └── restful_ressources.py
```

## Setup
### Prerequisites

- [docker](https://www.docker.com)

### Environment variables

```shell
cp .env.dist .env
```

This creates a local `.env`; keep it out of version control. PostgreSQL uses password authentication. For mounted secrets, set fields such as `JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret`; file-backed secret values take precedence over plaintext values. The sample JWT secret is accepted only when `APP_ENV=local`.

### Run the containers

```shell
docker compose up --build
```

This starts only the API, PostgreSQL, Redis, Alembic migration, and local seed step. The admin account is created idempotently only when `APP_ENV=local`.

## Default admin account

For local development, the seed command creates one admin user after migrations:

| Email           | Password  |
|-----------------|-----------|
| test@admin.com  | Cloud.456 |

Get a JWT by calling `POST /v1/token` with form body `username=test@admin.com` and `password=Cloud.456`, then use the returned `access_token` as `Authorization: Bearer <token>` for admin endpoints. The seed command exits without creating an account outside local mode. The forward Alembic migration removes only the original account with its unchanged password hash; it preserves customized accounts.

## Test the API

You can check the Swagger documentation on [localhost:8000](http://localhost:8000).

```shell
curl localhost:8000/v1/health
```

`/v1/health` remains the compatibility alias for liveness. `/v1/health/live` checks that the process responds; `/v1/health/ready` checks PostgreSQL and Redis and returns `503` if either is unavailable. Metrics are exposed at `/metrics`; each response includes `X-Request-ID`, and application request logs are JSON. Set `OTEL_ENABLED=true` and configure `OTEL_EXPORTER_OTLP_ENDPOINT` to enable traces.

```shell
curl localhost:8000/v1/health/live
curl localhost:8000/v1/health/ready
```

The liveness response is:

```
{"alive":true, "status":"ok"}
```

## Test the database

```shell
docker compose exec mars_db psql -U mars -d mars
```

This command will take you inside the PostgreSQL database container where you can apply any SQL command you want.

```
psql (16.x)
Type "help" for help.

mars=# \d
        List of relations
 Schema | Name | Type  |  Owner
--------+------+-------+---------
 public | user | table | mars
```

## How to add database migrations

Schema changes flow from SQLAlchemy models through Alembic:

1. Update or add models under `src/models/`.
2. Autogenerate a revision against a running database:

```shell
docker compose up -d mars_db
alembic revision --autogenerate -m "describe_change"
```

3. Review the generated script in `alembic/versions/`, then apply:

```shell
docker compose up --build --abort-on-container-exit mars_migrate
# or locally: alembic upgrade head
```

Applied revisions are immutable: add a new revision for schema or data changes. Existing seed history is retained. The local seed command creates the default admin only when the account is absent and `APP_ENV=local`.

To roll back one revision:

```shell
alembic downgrade -1
```

See the [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/tutorial.html) for more.

## Integration and Unit Testing

One of important things that should be in every project is tests to keeps thing organized and make sure everything is working as intended.

### Integration tests
Here's how to run the integration test locally:

```shell
docker compose --profile test up --build --abort-on-container-exit --exit-code-from mars_integration_tests mars_integration_tests
```

### Unit tests
Here's how to run the unit tests locally:

```shell
docker compose --profile test up --build --abort-on-container-exit mars_unit_tests
```

## Linter

Having a fast linter can help avoiding coding style problems, and potentially avoid future bugs that takes long hours to fix.
For the linter we're working with [ruff](https://astral.sh/ruff), a very fast linter written in Rust.

Here's how to run the linter test locally:

```shell
docker compose --profile test up --build --abort-on-container-exit mars_linter
```

## Security Scan

For our project, we're using `bandit`, a tool designed to find common security issues in Python code. Here's how to run it locally:

```shell
docker compose --profile test run --build --rm mars_security
```

Test and tooling services are under the `test` profile; the `ci/*.sh` wrappers enable it automatically.

## Optional worker and agent

The worker and agent do not start with the core stack:

```shell
# Worker only; run endpoints remain disabled
docker compose --profile worker up --build

# Full local agent stack, including the mock OpenAI-compatible LLM
MARS_AGENT_ENABLED=true docker compose --profile worker --profile agent up --build
```

With agent mode enabled, `POST /v1/runs` accepts a prompt and optional `token_budget`; `Idempotency-Key` avoids duplicate submissions. `GET /v1/runs/{id}` returns queued, running, completed, or failed state. Configure `LLM_BASE_URL` and `LLM_API_KEY` to use another OpenAI-compatible endpoint. Cache data uses Redis DB 0 and Celery broker/results use Redis DB 1.

## Pre-commit

Install hooks locally to catch lint issues before CI:

```shell
pip install pre-commit
pre-commit install --install-hooks
pre-commit run --all-files
```

## How to add a new endpoint

1. **Model** — add or update a SQLAlchemy model in `src/models/`.
2. **Alembic migration** — `alembic revision --autogenerate -m "description"`, review, then `alembic upgrade head`.
3. **Schema** — add Pydantic request/response schemas in `src/schemas/`.
4. **Controller** — implement logic in `src/controllers/`.
5. **Route** — wire the endpoint in `src/routes/` and register it in `src/restful_ressources.py`.
6. **Tests** — add coverage under `src/integration_tests/` (and `src/unit_tests/` when appropriate).

Run `./ci/integration-test.sh` after changes.

-------

## Contributions

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md).

Give a star if this project helped you!

## Related

- [Mercury](https://github.com/ayoub3bidi/mercury) — the original Flyway/SQL migration variant (unchanged).
