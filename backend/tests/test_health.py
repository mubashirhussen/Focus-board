from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_observability():
    # 1. Health liveness
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert "X-Request-ID" in res.headers

    # 2. Ready probe
    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "ready"
    assert "X-Request-ID" in ready_res.headers

    # 3. Correlation ID preservation
    custom_id = "test-custom-request-id-12345"
    custom_res = client.get("/health", headers={"X-Request-ID": custom_id})
    assert custom_res.headers["X-Request-ID"] == custom_id
