from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_is_explicit_when_models_are_not_ready():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "source_ready" in body
    assert "checkpoint_ready" in body
    assert "ready" in body
    assert body["ready"] == (body["source_ready"] and body["checkpoint_ready"])


def test_tracking_health_is_explicit():
    response = client.get("/api/tracking/health")
    assert response.status_code == 200
    body = response.json()
    assert "configured" in body
    assert "model_exists" in body
    assert "identity_mode" in body
