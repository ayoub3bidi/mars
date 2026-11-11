# Changelog

All notable changes to Mars are documented here.

## [v0.1.5] - 2026-11-11

### Added

- Optional asynchronous agent runs through `POST /v1/runs` and `GET /v1/runs/{id}`, with idempotency keys, configurable token budgets, and a local mock LLM for development.
- An opt-in Celery worker and agent service profile, plus request IDs, structured request logging, Prometheus metrics, and optional OpenTelemetry tracing.
- Liveness and readiness health endpoints for deployment checks.

### Changed

- Added the `runs` table through an Alembic migration. Existing migration history remains intact.
- Production checks now reject unsafe default credentials while retaining a local-only development seed account.
- Updated FastAPI, ASN.1-related dependencies, and CI image scanning configuration.

### Fixed

- Aligned Prometheus instrumentation with FastAPI so runtime metrics are collected consistently.
