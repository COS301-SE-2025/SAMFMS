"""
Exception handlers for GPS service
"""
import logging
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas.responses import ResponseBuilder

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Database connection error"""
    pass


class EventPublishError(Exception):
    """Event publishing error"""
    pass


class BusinessLogicError(Exception):
    """Business logic error"""
    pass


async def database_connection_error_handler(request: Request, exc: DatabaseConnectionError):
    """Handle database connection errors"""
    logger.error(f"Database connection error: {exc}")
    
    error_response = ResponseBuilder.error(
        error="database_connection_error",
        message="Database connection failed. Please try again later.",
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=503,
        content=error_response.model_dump()
    )


async def event_publish_error_handler(request: Request, exc: EventPublishError):
    """Handle event publishing errors"""
    logger.error(f"Event publish error: {exc}")
    
    error_response = ResponseBuilder.error(
        error="event_publish_error",
        message="Failed to publish event. Operation completed but notification may be delayed.",
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=202,  # Accepted but with warning
        content=error_response.model_dump()
    )


async def business_logic_error_handler(request: Request, exc: BusinessLogicError):
    """Handle business logic errors"""
    logger.error(f"Business logic error: {exc}")
    
    error_response = ResponseBuilder.error(
        error="business_logic_error",
        message=str(exc),
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=400,
        content=error_response.model_dump()
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc}")
    
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = ResponseBuilder.validation_error(
        message="Request validation failed",
        validation_errors=validation_errors,
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    error_response = ResponseBuilder.error(
        error="http_error",
        message=exc.detail,
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = ResponseBuilder.error(
        error="internal_server_error",
        message="An unexpected error occurred. Please try again later.",
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


# Exception handler mapping
EXCEPTION_HANDLERS = {
    DatabaseConnectionError: database_connection_error_handler,
    EventPublishError: event_publish_error_handler,
    BusinessLogicError: business_logic_error_handler,
    RequestValidationError: validation_error_handler,
    HTTPException: http_exception_handler,
    StarletteHTTPException: http_exception_handler,
    Exception: general_exception_handler,
}
