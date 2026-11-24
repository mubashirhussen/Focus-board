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
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
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
    automation_routes,
    integration_platform_routes,
    observability_routes,
    data_intelligence_routes,
    security_intelligence_routes,
    product_lifecycle_routes,
    organization_routes,
    project_routes,
    board_routes,
    view_routes,
    filter_routes,
    reminder_routes,
    team_routes,
    comment_routes,
    activity_routes,
    cx_intelligence_routes,
    time_tracking_routes,
    goal_routes,
)

# Configure structured, sensitive-data-safe logging
logger = setup_logging()

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

# Register centralized exception handlers
register_exception_handlers(app)

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
app.include_router(health_routes.router, prefix=settings.API_V1_STR)
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
app.include_router(intelligence_routes.router)  # Direct /intelligence/... access support
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
app.include_router(financial_intelligence_routes.router)  # Direct /finance/... access support
app.include_router(strategic_intelligence_routes.router, prefix=settings.API_V1_STR)
app.include_router(strategic_intelligence_routes.router)  # Direct /strategy/... access support
app.include_router(innovation_lab_routes.router, prefix=settings.API_V1_STR)
app.include_router(knowledge_intelligence_routes.router, prefix=settings.API_V1_STR)
app.include_router(automation_routes.router, prefix=settings.API_V1_STR)
app.include_router(integration_platform_routes.router, prefix=settings.API_V1_STR)
app.include_router(observability_routes.router, prefix=settings.API_V1_STR)
app.include_router(data_intelligence_routes.router, prefix=settings.API_V1_STR)
app.include_router(data_intelligence_routes.router)  # Direct /data-intelligence/... access support
app.include_router(security_intelligence_routes.router, prefix=f"{settings.API_V1_STR}/security-intelligence")
app.include_router(security_intelligence_routes.router, prefix="/security-intelligence")  # Direct /security-intelligence/... access support
app.include_router(product_lifecycle_routes.router, prefix=f"{settings.API_V1_STR}/product-lifecycle")
app.include_router(product_lifecycle_routes.router, prefix="/product-lifecycle")
app.include_router(organization_routes.router, prefix=settings.API_V1_STR)
app.include_router(project_routes.router, prefix=settings.API_V1_STR)
app.include_router(board_routes.router, prefix=settings.API_V1_STR)
app.include_router(view_routes.router, prefix=settings.API_V1_STR)
app.include_router(filter_routes.router, prefix=settings.API_V1_STR)
app.include_router(reminder_routes.router, prefix=settings.API_V1_STR)
app.include_router(team_routes.router, prefix=settings.API_V1_STR)
app.include_router(comment_routes.router, prefix=settings.API_V1_STR)
app.include_router(activity_routes.router, prefix=settings.API_V1_STR)
app.include_router(cx_intelligence_routes.router, prefix=settings.API_V1_STR)
app.include_router(cx_intelligence_routes.router)  # Direct /cx/... access support
app.include_router(time_tracking_routes.router, prefix=settings.API_V1_STR)
app.include_router(time_tracking_routes.router)  # Direct /time-tracking/... access support
app.include_router(goal_routes.router, prefix=settings.API_V1_STR)
app.include_router(goal_routes.router)  # Direct /goals/... access support

@app.get("/")
def root():
    return {
        "message": "FocusBoard API is live",
        "docs": "/docs",
        "version": settings.VERSION
    }
