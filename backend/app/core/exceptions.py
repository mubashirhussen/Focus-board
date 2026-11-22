import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("focusboard")

class FocusBoardException(Exception):
    """Base exception for application-level errors."""
    def __init__(self, message: str, code: str = "APPLICATION_ERROR", status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

class EntityNotFoundException(FocusBoardException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{entity_id}' was not found.",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )

class PermissionDeniedException(FocusBoardException):
    def __init__(self, message: str = "Access denied: You do not have permission to perform this action."):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN
        )

class ConflictException(FocusBoardException):
    def __init__(self, message: str, code: str = "RESOURCE_CONFLICT"):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT
        )

class ValidationException(FocusBoardException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class AuthenticationException(FocusBoardException):
    def __init__(self, message: str = "Authentication required or credentials invalid."):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

def register_exception_handlers(app: FastAPI) -> None:
    """Registers centralized, secure exception handlers on the FastAPI application."""

    @app.exception_handler(FocusBoardException)
    async def focusboard_exception_handler(request: Request, exc: FocusBoardException):
        req_id = getattr(request.state, "request_id", None)
        trace_id = getattr(request.state, "trace_id", None)
        logger.warning(f"Business Exception [{exc.code}] on {request.method} {request.url.path}: {exc.message} (ReqID: {req_id})")
        
        content = {
            "detail": exc.message,
            "code": exc.code,
            "request_id": req_id,
            "trace_id": trace_id
        }
        if exc.details:
            content["details"] = exc.details

        headers = {}
        if req_id:
            headers["X-Request-ID"] = req_id
        if trace_id:
            headers["X-Trace-ID"] = trace_id

        return JSONResponse(status_code=exc.status_code, content=content, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", None)
        trace_id = getattr(request.state, "trace_id", None)
        errors = []
        for err in exc.errors():
            loc = " -> ".join([str(l) for l in err.get("loc", [])])
            errors.append({"field": loc, "message": err.get("msg", "Invalid field value")})

        headers = {}
        if req_id:
            headers["X-Request-ID"] = req_id
        if trace_id:
            headers["X-Trace-ID"] = trace_id

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request payload validation failed.",
                "code": "VALIDATION_ERROR",
                "errors": errors,
                "request_id": req_id,
                "trace_id": trace_id
            },
            headers=headers
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        req_id = getattr(request.state, "request_id", None)
        trace_id = getattr(request.state, "trace_id", None)

        headers = {}
        if req_id:
            headers["X-Request-ID"] = req_id
        if trace_id:
            headers["X-Trace-ID"] = trace_id

        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": detail,
                "code": f"HTTP_{exc.status_code}",
                "request_id": req_id,
                "trace_id": trace_id
            },
            headers=headers
        )
