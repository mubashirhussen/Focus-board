import time
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

def test_api_latency_benchmarks(client):
    """Benchmark critical endpoint response times under typical operational load."""
    # 1. Health check latency (Target: < 50ms)
    t0 = time.perf_counter()
    res = client.get("/health")
    health_latency = (time.perf_counter() - t0) * 1000
    assert res.status_code == 200
    assert health_latency < 100, f"Health check took {health_latency:.2f}ms (threshold 100ms)"

    # 2. Registration & Authentication latency (Target: < 300ms including Bcrypt hashing)
    t0 = time.perf_counter()
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"name": "Perf User", "email": "perf@example.com", "password": "Password123!"}
    )
    auth_latency = (time.perf_counter() - t0) * 1000
    assert reg_res.status_code in [200, 201]
    token = reg_res.json()["access_token"]
    assert auth_latency < 500, f"Registration took {auth_latency:.2f}ms"

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Batch task creation latency
    task_count = 50
    t0 = time.perf_counter()
    for i in range(task_count):
        client.post(
            "/api/v1/tasks",
            json={"title": f"Benchmark Task #{i}", "priority": "Medium", "status": "Todo"},
            headers=headers
        )
    batch_create_duration = (time.perf_counter() - t0) * 1000
    avg_per_task = batch_create_duration / task_count
    assert avg_per_task < 50, f"Average task creation took {avg_per_task:.2f}ms (threshold 50ms)"

    # 4. Large collection fetch & pagination latency (Target: < 100ms for 50 records)
    t0 = time.perf_counter()
    list_res = client.get("/api/v1/tasks", headers=headers)
    list_latency = (time.perf_counter() - t0) * 1000
    assert list_res.status_code == 200
    assert len(list_res.json()) == task_count
    assert list_latency < 150, f"Listing 50 tasks took {list_latency:.2f}ms (threshold 150ms)"

    # 5. Search response latency (Target: < 100ms)
    t0 = time.perf_counter()
    search_res = client.get("/api/v1/search?q=Benchmark", headers=headers)
    search_latency = (time.perf_counter() - t0) * 1000
    assert search_res.status_code == 200
    assert len(search_res.json()["results"]) == 20
    assert search_res.json()["total"] == task_count
    assert search_latency < 150, f"Search took {search_latency:.2f}ms (threshold 150ms)"

    # 6. Analytics computation latency
    t0 = time.perf_counter()
    analytics_res = client.get("/api/v1/analytics/summary", headers=headers)
    analytics_latency = (time.perf_counter() - t0) * 1000
    assert analytics_res.status_code == 200
    assert analytics_latency < 150, f"Analytics summary took {analytics_latency:.2f}ms"
