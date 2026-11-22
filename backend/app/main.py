import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import engine, Base
import app.models  # Ensure models are loaded
from app.api.routes import auth_routes, task_routes, analytics_routes, health_routes

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ReqID: %(name)s] %(message)s"
)
logger = logging.getLogger("focusboard")

# Initialize DB tables for SQLite / fallback
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FocusBoard Multi-User Task Management & Analytics API"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Correlation Request ID and Structured Logging Middleware
@app.middleware("http")
async def correlation_id_and_logging_middleware(request: Request, call_next):
    # Extract or generate correlation ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()
    logger.info(f"Incoming: {request.method} {request.url.path} (ID: {request_id})")

    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(f"Completed: {request.method} {request.url.path} -> Status {response.status_code} in {duration_ms}ms (ID: {request_id})")
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"Unhandled Exception: {request.method} {request.url.path} in {duration_ms}ms: {exc} (ID: {request_id})")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
            headers={"X-Request-ID": request_id}
        )

# Register API Routers
app.include_router(health_routes.router)
app.include_router(auth_routes.router, prefix=settings.API_V1_STR)
app.include_router(task_routes.router, prefix=settings.API_V1_STR)
app.include_router(analytics_routes.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "FocusBoard API is live",
        "docs": "/docs",
        "version": settings.VERSION
    }
