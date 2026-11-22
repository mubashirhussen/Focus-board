import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

def test_correlation_headers_and_trace_id(client):
    """Verify that every request generates and propagates X-Request-ID and X-Trace-ID headers."""
    # 1. Without client-provided headers
    res = client.get("/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert "X-Trace-ID" in res.headers
    assert res.headers["X-Trace-ID"].startswith("trace-")

    # 2. With client-provided correlation IDs
    custom_req_id = "req-custom-test-12345"
    custom_trace_id = "trace-custom-test-67890"
    res_custom = client.get(
        "/health",
        headers={"X-Request-ID": custom_req_id, "X-Trace-ID": custom_trace_id}
    )
    assert res_custom.status_code == 200
    assert res_custom.headers["X-Request-ID"] == custom_req_id
    assert res_custom.headers["X-Trace-ID"] == custom_trace_id

def test_metrics_prometheus_endpoint(client):
    """Verify that /metrics exports valid Prometheus format observability metrics."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers["content-type"]
    body = res.text
    assert "focusboard_uptime_seconds" in body
    assert "focusboard_database_connected 1" in body
    assert "focusboard_api_status 1" in body

def test_readiness_probe_db_failure_simulation():
    """Verify that /ready returns HTTP 503 if the database engine throws an error."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Simulated connection timeout to PostgreSQL cluster")

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with TestClient(app) as test_client:
            res = test_client.get("/ready")
            assert res.status_code == 503
            data = res.json()
            assert "Database connection error" in data["detail"]
    finally:
        app.dependency_overrides.clear()

def test_unhandled_route_rejection(client):
    """Verify that unknown routes return 404 without leaking server tracebacks."""
    res = client.get("/api/v1/non_existent_endpoint_xyz")
    assert res.status_code == 404
    assert "detail" in res.json()
    assert "X-Request-ID" in res.headers
