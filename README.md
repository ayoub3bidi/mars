# Mars
<p align="center">
    <img src="./src/assets/mars.png"/> <br/>
    Pythonista backend boilerplate. Alembic migrations, SQLAlchemy-native schema
</p>

<p align="center">
    <img src="https://img.shields.io/badge/Made%20with-Python-1f425f.svg">
    <img src="https://img.shields.io/github/release/ayoub3bidi/mars">
</p>

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
- [PostgreSQL](https://hub.docker.com/_/postgres) as its main database, [Redis](https://hub.docker.com/_/redis) for caching, and [Alembic](https://alembic.sqlalchemy.org/) for database migrations.
- Unit and integration tests.
- Security scanner (Bandit).

## Docker Hub image

A pre-built API image is published on Docker Hub and updated on each push to `main`:

- **Repository:** [ayoub3bidi/mars](https://hub.docker.com/r/ayoub3bidi/mars)

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

This will create a `.env` file in your project locally.

```shell
APP_TITLE="Mars API Docs"
APP_DESCRIPTION="This is the Swagger documentation of the Mars API"
APP_VERSION=0.4.0
API_URL="http://localhost:8000"
API_VERSION="v1"
APP_ENV=local
## Postgres Configuration
POSTGRES_HOST=mars_db
POSTGRES_PASSWORD=mars
POSTGRES_PORT=5432
POSTGRES_USER=mars
POSTGRES_DB=mars
POSTGRES_HOST_AUTH_METHOD=trust
POSTGRES_SIZE_POOL=30
POSTGRES_MAX_OVERFLOW=10
POSTGRES_POOL_TIMEOUT=30
POSTGRES_POOL_RECYCLE=1800
## Redis Configuration
REDIS_HOST=mars_cache
REDIS_PORT=6379
## JWT Configuration
JWT_SECRET_KEY="mysecretkey"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
## OIDC Configuration
OIDC_GOOGLE_CLIENT_ID="changeme"
OIDC_GOOGLE_CLIENT_SECRET="changeme"
GOOGLE_AUTH_URL="https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL="https://accounts.google.com/o/oauth2/token"
GOOGLE_USER_INFO_URL="https://www.googleapis.com/oauth2/v1/userinfo"
```

### Run the containers

```shell
docker compose up --build --force-recreate
```

## Default admin account

Migrations seed one admin user so you can try the API and admin routes right away:

| Email           | Password  |
|-----------------|-----------|
| test@admin.com  | Cloud.456 |

Get a JWT by calling `POST /v1/token` with form body `username=test@admin.com` and `password=Cloud.456`, then use the returned `access_token` as `Authorization: Bearer <token>` for admin endpoints. Change or remove this user in production.

## Test the API

You can check the Swagger documentation on [localhost:8000](http://localhost:8000).

![Swagger page](./src/assets/swagger.png)

```shell
curl localhost:8000/v1/health
```

This will check the health of the API. The result should be like this:

```
{"alive":true, "status":"ok"}
```

## Test the database

```shell
docker exec -it mars_db psql -U mars
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
docker compose up --build --abort-on-container-exit mars_integration_tests
```

### Unit tests
Here's how to run the unit tests locally:

```shell
docker compose up --build --abort-on-container-exit mars_unit_tests
```

## Linter

Having a fast linter can help avoiding coding style problems, and potentially avoid future bugs that takes long hours to fix.
For the linter we're working with [ruff](https://astral.sh/ruff), a very fast linter written in Rust.

Here's how to run the linter test locally:

```shell
docker compose up --build --abort-on-container-exit mars_linter
```

## Security Scan

For our project, we're using `bandit`, a tool designed to find common security issues in Python code. Here's how to run it locally:

```shell
docker compose up --build --abort-on-container-exit mars_security
```

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
