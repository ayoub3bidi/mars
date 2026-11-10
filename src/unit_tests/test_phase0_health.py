import pytest
from fastapi import HTTPException

import routes.health as health


def test_liveness_alias_matches_legacy_health():
    assert health.get_liveness() == health.get_health() == {"status": "ok", "alive": True}


@pytest.mark.parametrize(
    ("postgres_ok", "redis_ok", "expected"),
    [(True, False, {"postgres": True, "redis": False}), (False, True, {"postgres": False, "redis": True})],
)
def test_readiness_returns_503_when_dependency_fails(monkeypatch, postgres_ok, redis_ok, expected):
    class Connection:
        def execute(self, _query):
            if not postgres_ok:
                raise ConnectionError("postgres unavailable")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class Database:
        @staticmethod
        def connect():
            if not postgres_ok:
                raise ConnectionError("postgres unavailable")
            return Connection()

    class Redis:
        @staticmethod
        def ping():
            if not redis_ok:
                raise ConnectionError("redis unavailable")
            return True

    monkeypatch.setattr(health, "dbEngine", Database())
    monkeypatch.setattr(health, "redis_connect", Redis())

    with pytest.raises(HTTPException) as error:
        health.get_readiness()

    assert error.value.status_code == 503
    assert error.value.detail["checks"] == expected


def test_readiness_succeeds_when_dependencies_are_available(monkeypatch):
    class Connection:
        def execute(self, _query):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class Database:
        @staticmethod
        def connect():
            return Connection()

    class Redis:
        @staticmethod
        def ping():
            return True

    monkeypatch.setattr(health, "dbEngine", Database())
    monkeypatch.setattr(health, "redis_connect", Redis())
    assert health.get_readiness() == {
        "status": "ok",
        "ready": True,
        "checks": {"postgres": True, "redis": True},
    }
