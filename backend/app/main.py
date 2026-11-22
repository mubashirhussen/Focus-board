import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limiter import RateLimiterMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.database import engine, Base
import app.models  # Ensure all models are registered
from app.services.entitlement_service import seed_default_plans
from app.api.routes import (
    auth_routes,
    task_routes,
    analytics_routes,
    health_routes,
    ai_routes,
    notification_routes,
    workspace_routes,
    websocket_routes,
    search_routes,
    audit_routes,
    billing_routes,
    integration_routes,
    calendar_routes,
    workflow_routes,
    push_routes,
    intelligence_routes,
    enterprise_routes,
    growth_routes,
    support_routes,
    ai_agent_routes,
    regional_routes,
    enterprise_analytics_routes,
    developer_routes,
    public_api_routes,
    security_compliance_routes,
    financial_intelligence_routes,
    strategic_intelligence_routes,
    innovation_lab_routes,
    knowledge_intelligence_routes,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ReqID: %(name)s] %(message)s"
)
logger = logging.getLogger("focusboard")

# Initialize DB tables for SQLite / fallback
Base.metadata.create_all(bind=engine)

# Seed default plans on startup
try:
    with Session(bind=engine) as init_db:
        seed_default_plans(init_db)
except Exception as exc:
    logger.warning(f"Could not seed default plans: {exc}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FocusBoard Enterprise SaaS Task Management & Connected Platform API"
)

# 1. Security Headers Middleware (OWASP protection)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Trace-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"]
)

# 3. Rate Limiter Middleware
app.add_middleware(RateLimiterMiddleware, enabled=True)

# 4. Correlation Request ID, Distributed Tracing and Structured Logging Middleware
app_metrics = {
    "requests_total": 0,
    "errors_total": 0,
    "latency_ms_sum": 0.0,
    "start_time": time.time(),
}

@app.middleware("http")
async def correlation_id_and_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_id = request.headers.get("X-Trace-ID") or f"trace-{uuid.uuid4().hex[:16]}"
    request.state.request_id = request_id
    request.state.trace_id = trace_id

    start_time = time.time()
    app_metrics["requests_total"] += 1
    logger.info(f"Incoming: {request.method} {request.url.path} (ID: {request_id}, Trace: {trace_id})")

    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        app_metrics["latency_ms_sum"] += duration_ms

        if response.status_code >= 500:
            app_metrics["errors_total"] += 1

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        logger.info(f"Completed: {request.method} {request.url.path} -> Status {response.status_code} in {duration_ms}ms (ID: {request_id})")
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        app_metrics["latency_ms_sum"] += duration_ms
        app_metrics["errors_total"] += 1
        logger.error(f"Unhandled Exception: {request.method} {request.url.path} in {duration_ms}ms: {exc} (ID: {request_id}, Trace: {trace_id})")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id, "trace_id": trace_id},
            headers={"X-Request-ID": request_id, "X-Trace-ID": trace_id}
        )

# Register API Routers
app.include_router(health_routes.router)
app.include_router(auth_routes.router, prefix=settings.API_V1_STR)
app.include_router(task_routes.router, prefix=settings.API_V1_STR)
app.include_router(analytics_routes.router, prefix=settings.API_V1_STR)
app.include_router(ai_routes.router, prefix=settings.API_V1_STR)
app.include_router(notification_routes.router, prefix=settings.API_V1_STR)
app.include_router(workspace_routes.router, prefix=settings.API_V1_STR)
app.include_router(websocket_routes.router, prefix=settings.API_V1_STR)
app.include_router(search_routes.router, prefix=settings.API_V1_STR)
app.include_router(audit_routes.router, prefix=settings.API_V1_STR)
app.include_router(billing_routes.router, prefix=settings.API_V1_STR)
app.include_router(integration_routes.router, prefix=settings.API_V1_STR)
app.include_router(calendar_routes.router, prefix=settings.API_V1_STR)
app.include_router(workflow_routes.router, prefix=settings.API_V1_STR)
app.include_router(push_routes.router, prefix=settings.API_V1_STR)
app.include_router(intelligence_routes.router, prefix=settings.API_V1_STR)
app.include_router(enterprise_routes.router, prefix=settings.API_V1_STR)
app.include_router(growth_routes.router, prefix=settings.API_V1_STR)
app.include_router(support_routes.router, prefix=settings.API_V1_STR)
app.include_router(ai_agent_routes.router, prefix=settings.API_V1_STR)
app.include_router(regional_routes.router, prefix=settings.API_V1_STR)
app.include_router(enterprise_analytics_routes.router, prefix=settings.API_V1_STR)
app.include_router(developer_routes.router, prefix=settings.API_V1_STR)
app.include_router(public_api_routes.router, prefix=settings.API_V1_STR)
app.include_router(public_api_routes.router)  # Direct /public/v1/... access support
app.include_router(security_compliance_routes.router, prefix=settings.API_V1_STR)
app.include_router(financial_intelligence_routes.router, prefix=settings.API_V1_STR)
app.include_router(strategic_intelligence_routes.router, prefix=settings.API_V1_STR)
app.include_router(innovation_lab_routes.router, prefix=settings.API_V1_STR)
app.include_router(knowledge_intelligence_routes.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "FocusBoard API is live",
        "docs": "/docs",
        "version": settings.VERSION
    }
