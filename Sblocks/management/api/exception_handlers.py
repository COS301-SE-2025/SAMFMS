"""
Global exception handlers for Management service
"""
import logging
import traceback
import json
from datetime import datetime
from typing import Any

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas.responses import ResponseBuilder, ErrorResponse
from api.dependencies import get_request_id
from config.rabbitmq_config import json_serializer

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions"""
    try:
        request_id = await get_request_id(request)
        
        # Log the full exception
        logger.error(
            f"Unhandled exception in {request.method} {request.url}: {exc}",
            extra={
                "request_id": request_id,
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
                "traceback": traceback.format_exc()
            }
        )
        
        # Build error response
        error_response = ResponseBuilder.error(
            error="InternalServerError",
            message="An internal server error occurred",
            details={
                "type": type(exc).__name__,
                "timestamp": datetime.utcnow().isoformat()
            },
            request_id=request_id,
            trace_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=json.loads(json.dumps(error_response.model_dump(), default=json_serializer))
        )
        
    except Exception as handler_exc:
        # Fallback if even the error handler fails
        logger.critical(f"Exception handler failed: {handler_exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": "CriticalError",
                "message": "Critical system error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for HTTP exceptions"""
    try:
        request_id = await get_request_id(request)
        
        # Log based on status code severity
        if exc.status_code >= 500:
            logger.error(f"HTTP {exc.status_code} in {request.method} {request.url}: {exc.detail}")
        elif exc.status_code >= 400:
            logger.warning(f"HTTP {exc.status_code} in {request.method} {request.url}: {exc.detail}")
        
        # Build error response
        error_response = ResponseBuilder.error(
            error="HTTPException",
            message=exc.detail,
            details={
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat()
            },
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=json.loads(json.dumps(error_response.model_dump(), default=json_serializer))
        )
        
    except Exception as handler_exc:
        logger.error(f"HTTP exception handler failed: {handler_exc}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for request validation errors"""
    try:
        request_id = await get_request_id(request)
        
        # Log validation errors
        logger.warning(
            f"Validation error in {request.method} {request.url}: {exc.errors()}",
            extra={"request_id": request_id}
        )
        
        # Build validation error response
        validation_errors = []
        for error in exc.errors():
            validation_errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input")
            })
        
        error_response = ResponseBuilder.validation_error(
            message="Request validation failed",
            validation_errors=validation_errors,
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=json.loads(json.dumps(error_response.model_dump(), default=json_serializer))
        )
        
    except Exception as handler_exc:
        logger.error(f"Validation exception handler failed: {handler_exc}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Validation failed"}
        )


async def starlette_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for Starlette HTTP exceptions"""
    try:
        request_id = await get_request_id(request)
        
        logger.warning(f"Starlette HTTP {exc.status_code} in {request.method} {request.url}: {exc.detail}")
        
        error_response = ResponseBuilder.error(
            error="HTTPError",
            message=exc.detail,
            details={
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat()
            },
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=json.loads(json.dumps(error_response.model_dump(), default=json_serializer))
        )
        
    except Exception as handler_exc:
        logger.error(f"Starlette exception handler failed: {handler_exc}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )


class DatabaseConnectionError(Exception):
    """Custom exception for database connection issues"""
    pass


class EventPublishError(Exception):
    """Custom exception for event publishing failures"""
    pass


class BusinessLogicError(Exception):
    """Custom exception for business logic violations"""
    pass


async def database_exception_handler(request: Request, exc: DatabaseConnectionError) -> JSONResponse:
    """Handler for database connection errors"""
    try:
        request_id = await get_request_id(request)
        
        logger.error(f"Database connection error: {exc}")
        
        error_response = ResponseBuilder.error(
            error="DatabaseError",
            message="Database service temporarily unavailable",
            details={"timestamp": datetime.utcnow().isoformat()},
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=json.loads(json.dumps(error_response.model_dump(), default=json_serializer))
        )
        
    except Exception as handler_exc:
        logger.error(f"Database exception handler failed: {handler_exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Service unavailable"}
        )


async def event_publish_exception_handler(request: Request, exc: EventPublishError) -> JSONResponse:
    """Handler for event publishing errors"""
    try:
        request_id = await get_request_id(request)
        
        logger.error(f"Event publishing error: {exc}")
        
        error_response = ResponseBuilder.error(
            error="EventPublishError",
            message="Event publishing failed - operation completed but notifications may be delayed",
            details={"timestamp": datetime.utcnow().isoformat()},
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_207_MULTI_STATUS,
            content=json.loads(json.dumps(error_response.model_dump(), default=json_serializer))
        )
        
    except Exception as handler_exc:
        logger.error(f"Event publish exception handler failed: {handler_exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Event system error"}
        )


async def business_logic_exception_handler(request: Request, exc: BusinessLogicError) -> JSONResponse:
    """Handler for business logic errors"""
    try:
        request_id = await get_request_id(request)
        
        logger.warning(f"Business logic error: {exc}")
        
        error_response = ResponseBuilder.error(
            error="BusinessLogicError",
            message=str(exc),
            details={"timestamp": datetime.utcnow().isoformat()},
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json.loads(json.dumps(error_response.model_dump(), default=json_serializer))
        )
        
    except Exception as handler_exc:
        logger.error(f"Business logic exception handler failed: {handler_exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": str(exc)}
        )


# Exception handler registry
EXCEPTION_HANDLERS = {
    Exception: global_exception_handler,
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    StarletteHTTPException: starlette_exception_handler,
    DatabaseConnectionError: database_exception_handler,
    EventPublishError: event_publish_exception_handler,
    BusinessLogicError: business_logic_exception_handler,
}
