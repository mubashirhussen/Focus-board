import pytest
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

def test_analytics_and_csv_export(client):
    # Register user
    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "Dana Scully", "email": "dana@example.com", "password": "password123"}
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add 2 tasks: 1 Completed, 1 In Progress with potential formula injection title
    client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "=cmd|' /C calc'!A0", "category": "Security", "status": "Completed"}
    )
    client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Design Specs", "category": "Design", "status": "In Progress"}
    )

    # 1. Summary
    summary = client.get("/api/v1/analytics/summary", headers=headers)
    assert summary.status_code == 200
    s_data = summary.json()
    assert s_data["total"] == 2
    assert s_data["completed"] == 1
    assert s_data["in_progress"] == 1
    assert s_data["completion_rate"] == 50

    # 2. Trends
    trends = client.get("/api/v1/analytics/completion-trends?days=7", headers=headers)
    assert trends.status_code == 200
    assert len(trends.json()) == 7

    # 3. Distribution
    dist = client.get("/api/v1/analytics/distribution", headers=headers)
    assert dist.status_code == 200
    assert len(dist.json()["by_status"]) >= 2

    # 4. Insights
    insights = client.get("/api/v1/analytics/insights", headers=headers)
    assert insights.status_code == 200
    assert len(insights.json()["insights"]) > 0

    # 5. CSV Export and formula injection check
    export = client.get("/api/v1/analytics/export", headers=headers)
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    csv_text = export.text
    # Verify the formula injection '=' was sanitized with leading single quote
    assert "'=cmd|' /C calc'!A0" in csv_text
