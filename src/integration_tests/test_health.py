import os

import pytest

from init_test import client

v = os.getenv("API_VERSION", "v1")


def test_get_health():
    if client is None:
        pytest.skip("Client not initialized")

    response = client.get(f"/{v}/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "alive": True,
    }


def test_live_endpoint_and_legacy_alias():
    if client is None:
        pytest.skip("Client not initialized")

    legacy = client.get(f"/{v}/health")
    live = client.get(f"/{v}/health/live")
    assert legacy.status_code == live.status_code == 200
    assert legacy.json() == live.json() == {"status": "ok", "alive": True}


def test_readiness_checks_dependencies():
    if client is None:
        pytest.skip("Client not initialized")

    response = client.get(f"/{v}/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "ready": True,
        "checks": {"postgres": True, "redis": True},
    }


def test_request_id_header_and_metrics_endpoint():
    if client is None:
        pytest.skip("Client not initialized")

    response = client.get(f"/{v}/health/live", headers={"X-Request-ID": "mars-e2e-request"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "mars-e2e-request"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text
