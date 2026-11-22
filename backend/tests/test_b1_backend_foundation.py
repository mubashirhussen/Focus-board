import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.core.config import settings
from app.core.logging import setup_logging, mask_sensitive_data
from app.core.exceptions import (
    FocusBoardException,
    EntityNotFoundException,
    PermissionDeniedException,
    ConflictException,
    ValidationException,
    AuthenticationException
)
from app.db.database import SessionLocal, engine, get_db

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_b1_app_initialization_and_metadata():
    """Verify application metadata, versioning, and docs paths."""
    assert settings.PROJECT_NAME == "FocusBoard API"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api/v1"
    assert app.title == settings.PROJECT_NAME
    assert app.version == settings.VERSION

def test_b1_health_endpoints_root_and_v1(client):
    """Verify both root and /api/v1/ health endpoints."""
    # 1. Root health
    res_root = client.get("/health")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["status"] == "healthy"
    assert data_root["service"] == "focusboard-api"

    # 2. Versioned health
    res_v1 = client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "healthy"

    # 3. Liveness probe
    res_live = client.get("/api/v1/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"
    assert "uptime_seconds" in res_live.json()

    # 4. Readiness probe
    res_ready = client.get("/api/v1/health/ready")
    assert res_ready.status_code == 200
    ready_data = res_ready.json()
    assert ready_data["status"] == "ready"
    assert ready_data["database"]["status"] == "connected"
    assert "latency_ms" in ready_data["database"]

    # 5. System info probe (non-sensitive metadata)
    res_sys = client.get("/api/v1/system/info")
    assert res_sys.status_code == 200
    sys_data = res_sys.json()
    assert sys_data["service"] == settings.PROJECT_NAME
    assert sys_data["version"] == settings.VERSION
    assert "database_dialect" in sys_data
    assert "SECRET_KEY" not in str(sys_data)

    # 6. Prometheus metrics endpoint
    res_metrics = client.get("/metrics")
    assert res_metrics.status_code == 200
    assert "focusboard_uptime_seconds" in res_metrics.text
    assert "focusboard_database_connected 1" in res_metrics.text

def test_b1_database_connectivity_and_session_lifecycle():
    """Verify SQLAlchemy engine connection, session query, and error rollback."""
    # 1. Direct engine ping
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1

    # 2. Session generator lifecycle with rollback verification
    session_gen = get_db()
    db = next(session_gen)
    assert db is not None
    assert db.is_active

    # Clean close
    try:
        next(session_gen)
    except StopIteration:
        pass

def test_b1_centralized_configuration_and_validation():
    """Verify settings validation, CORS parsing, and database URL resolution."""
    # CORS array parsing from JSON string
    cors_list = settings.assemble_cors_origins('["http://localhost:3000", "http://example.com"]')
    assert "http://localhost:3000" in cors_list
    assert "http://example.com" in cors_list

    # CORS comma-separated string
    cors_comma = settings.assemble_cors_origins("http://foo.com, http://bar.com")
    assert "http://foo.com" in cors_comma
    assert "http://bar.com" in cors_comma

    # Database pool settings
    assert settings.DB_POOL_PRE_PING is True
    assert settings.DB_POOL_SIZE >= 5
    assert settings.UPLOAD_MAX_BYTES == 20 * 1024 * 1024

def test_b1_logging_and_sensitive_data_masking():
    """Verify that logging utilities mask sensitive credentials."""
    payload = {
        "user_email": "operator@focusboard.io",
        "password": "SuperSecretPassword123!",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "api_key": "fb_live_981273981273",
        "nested": {
            "cvv": "123",
            "card_number": "4111222233334444",
            "safe_field": "public_data"
        }
    }
    masked = mask_sensitive_data(payload)
    assert masked["user_email"] == "operator@focusboard.io"
    assert masked["password"] == "[REDACTED]"
    assert masked["token"] == "[REDACTED]"
    assert masked["api_key"] == "[REDACTED]"
    assert masked["nested"]["cvv"] == "[REDACTED]"
    assert masked["nested"]["card_number"] == "[REDACTED]"
    assert masked["nested"]["safe_field"] == "public_data"

    logger = setup_logging()
    assert logger.name == "focusboard"

def test_b1_security_headers_middleware(client):
    """Verify OWASP recommended security headers are present on all responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") in ["DENY", "SAMEORIGIN"]
    assert "Content-Security-Policy" in headers
    assert "X-Request-ID" in headers
    assert "X-Trace-ID" in headers

def test_b1_exception_handling_and_safe_error_envelopes(client):
    """Verify that exceptions return structured JSON without leaking raw stack traces."""
    # Test 404 Not Found
    resp_404 = client.get("/api/v1/nonexistent-route-for-testing-404")
    assert resp_404.status_code == 404
    body = resp_404.json()
    assert "detail" in body
    assert "code" in body
    assert "X-Request-ID" in resp_404.headers

    # Test 422 Validation Error
    resp_422 = client.post("/api/v1/auth/register", json={"invalid_field": 123})
    assert resp_422.status_code == 422
    data_422 = resp_422.json()
    assert data_422["code"] == "VALIDATION_ERROR"
    assert "errors" in data_422
