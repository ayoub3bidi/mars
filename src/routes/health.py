from fastapi import APIRouter
import logging

from fastapi import HTTPException, status
from sqlalchemy import text

from database.postgres_db import dbEngine
from database.redis_db import redis_connect

router = APIRouter()


@router.get("/health")
def get_health():
    return {"status": "ok", "alive": True}


@router.get("/health/live")
def get_liveness():
    return get_health()


@router.get("/health/ready")
def get_readiness():
    checks = {"postgres": False, "redis": False}
    try:
        with dbEngine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["postgres"] = True
    except Exception as exc:
        logging.getLogger(__name__).warning("Postgres readiness check failed: %s", exc)

    try:
        checks["redis"] = bool(redis_connect.ping())
    except Exception as exc:
        logging.getLogger(__name__).warning("Redis readiness check failed: %s", exc)

    if not all(checks.values()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unavailable", "ready": False, "checks": checks},
        )
    return {"status": "ok", "ready": True, "checks": checks}
