# Mars Agent Guide

Mars is the FastAPI/SQLAlchemy variant of Mercury. Alembic revisions are the schema source of truth. Keep the default Compose stack to the API and its core dependencies; worker, agent, and test tools are opt-in profiles.

## Runtime map

- `src/app.py` starts Uvicorn; `src/main.py` creates the FastAPI app and lifespan.
- `src/routes/` exposes endpoints; controllers and repositories handle application/database work.
- `src/models/` and `alembic/versions/` define schema. Update models, generate/review a revision, and apply it with `alembic upgrade head`. Never edit an applied revision.
- `src/worker/` contains Celery configuration and task handling. `src/agent/graph.py` defines the LangGraph flow; the local OpenAI-compatible mock is in `src/agent/mock_llm.py`.
- `src/database/redis_db.py` connects cache operations to Redis DB 0. Celery uses DB 1.

## Interfaces and runtime behavior

- Health routes are mounted at `/{API_VERSION}/health`, `/health/live`, and `/health/ready`; the original route remains a liveness alias. Readiness checks Postgres and Redis.
- `/metrics` is enabled by default and can be disabled with `METRICS_ENABLED=false`. `OTEL_ENABLED=true` enables OTLP tracing.
- Every HTTP response includes `X-Request-ID`; application request logs are JSON.
- `MARS_AGENT_ENABLED=true` registers `POST /{API_VERSION}/runs` and `GET /{API_VERSION}/runs/{id}`. Runs use an optional `Idempotency-Key`; worker retry and late acknowledgement are configured in Celery.
- `src/seed_local_admin.py` creates the default admin only in local mode. Existing revisions are historical; a forward Alembic revision removes only the original email/hash pair.
- `src/main.py` does not create schema at startup. Compose runs Alembic before the API.

## Configuration and local commands

Copy `.env.dist` to `.env`. Secret values can be supplied with `JWT_SECRET_KEY_FILE`, `POSTGRES_PASSWORD_FILE`, `OIDC_GOOGLE_CLIENT_SECRET_FILE`, and `LLM_API_KEY_FILE`; file values override plaintext environment values. The default JWT secret is rejected whenever `APP_ENV` is not `local`.

```bash
docker compose up --build
docker compose --profile worker up --build
MARS_AGENT_ENABLED=true docker compose --profile worker --profile agent up --build
./ci/unit-test.sh
./ci/integration-test.sh
./ci/lint.sh
./ci/security.sh
```

Compose test and tooling services use the `test` profile. For local E2E checks, use an isolated Compose project, alternate host ports, and its disposable database volume; preserve the user's `.env` and existing volumes. Verify both core and agent experiences, migration behavior, cache/broker separation, and graceful request draining.

## Verification

The unit suite covers settings, health dependencies, run idempotency, and worker retry configuration. Integration tests exercise existing auth/admin flows, migration state, and health routes. CI runs unit/integration tests, Ruff, Bandit, and Trivy image scanning; the main branch publishes to Docker Hub and GHCR. No release tag is part of Phase 0 implementation.
