"""
Exception handlers for Trip Planning service
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Dict, Any

from schemas.responses import ResponseBuilder

logger = logging.getLogger(__name__)


class TripPlanningException(Exception):
    """Base exception for trip planning service"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class DatabaseConnectionError(TripPlanningException):
    """Database connection error"""
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, "DATABASE_CONNECTION_ERROR")


class EventPublishError(TripPlanningException):
    """Event publishing error"""
    def __init__(self, message: str = "Failed to publish event"):
        super().__init__(message, "EVENT_PUBLISH_ERROR")


class BusinessLogicError(TripPlanningException):
    """Business logic validation error"""
    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_LOGIC_ERROR")


class TripNotFoundError(TripPlanningException):
    """Trip not found error"""
    def __init__(self, trip_id: str):
        super().__init__(f"Trip {trip_id} not found", "TRIP_NOT_FOUND")


class DriverNotAvailableError(TripPlanningException):
    """Driver not available error"""
    def __init__(self, driver_id: str):
        super().__init__(f"Driver {driver_id} is not available", "DRIVER_NOT_AVAILABLE")


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error for {request.url}: {errors}")
    
    return JSONResponse(
        status_code=422,
        content=ResponseBuilder.validation_error(
            message="Request validation failed",
            validation_errors=errors
        ).model_dump(mode='json')
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code} error for {request.url}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseBuilder.error(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail
        ).model_dump(mode='json')
    )


async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions"""
    logger.warning(f"Starlette HTTP {exc.status_code} error for {request.url}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseBuilder.error(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail
        ).model_dump(mode='json')
    )


async def trip_planning_exception_handler(request: Request, exc: TripPlanningException):
    """Handle custom trip planning exceptions"""
    logger.error(f"Trip planning error for {request.url}: {exc.message}")
    
    status_code = 400
    if isinstance(exc, TripNotFoundError):
        status_code = 404
    elif isinstance(exc, DatabaseConnectionError):
        status_code = 503
    elif isinstance(exc, EventPublishError):
        status_code = 502
    
    return JSONResponse(
        status_code=status_code,
        content=ResponseBuilder.error(
            error=exc.error_code,
            message=exc.message
        ).model_dump(mode='json')
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error for {request.url}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ResponseBuilder.error(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred"
        ).model_dump(mode='json')
    )


# Exception handler mapping
EXCEPTION_HANDLERS: Dict[Any, Any] = {
    RequestValidationError: validation_exception_handler,
    HTTPException: http_exception_handler,
    StarletteHTTPException: starlette_exception_handler,
    TripPlanningException: trip_planning_exception_handler,
    Exception: general_exception_handler
}
