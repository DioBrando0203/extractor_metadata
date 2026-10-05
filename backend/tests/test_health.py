from fastapi.testclient import TestClient

from app.main import app


def test_health_is_local_and_stateless() -> None:
    response = TestClient(app, base_url="http://localhost").get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "storage": "none"}
