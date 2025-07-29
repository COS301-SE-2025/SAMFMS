"""
Response schemas for Trip Planning service
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    current_page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

class ResponseMeta(BaseModel):
    """Response metadata"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    version: str = Field(default="1.0.0", description="API version")
    pagination: Optional[PaginationMeta] = Field(None, description="Pagination information")

class StandardResponse(BaseModel):
    """Standard API response wrapper"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    status: ResponseStatus = Field(..., description="Response status")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")
    links: Optional[Dict[str, str]] = Field(None, description="Related links")

class ErrorResponse(BaseModel):
    """Error response schema"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    status: ResponseStatus = Field(default=ResponseStatus.ERROR, description="Response status")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")
    trace_id: Optional[str] = Field(None, description="Trace ID for debugging")

class ValidationErrorResponse(ErrorResponse):
    """Validation error response schema"""
    validation_errors: List[Dict[str, Any]] = Field(..., description="List of validation errors")


class SuccessResponse(StandardResponse):
    """Success response schema"""
    status: ResponseStatus = Field(default=ResponseStatus.SUCCESS, description="Response status")


class ListResponse(SuccessResponse):
    """List response with pagination"""
    data: List[Any] = Field(..., description="List of items")
    
    @property
    def total_items(self) -> int:
        """Get total items from pagination metadata"""
        return self.meta.pagination.total_items if self.meta.pagination else len(self.data)

class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    status: str = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    components: Dict[str, str] = Field(..., description="Component health status")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")


class ResponseBuilder:
    """Utility class for building standardized responses"""
    
    @staticmethod
    def success(
        data: Any = None, 
        message: Optional[str] = None,
        request_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        pagination: Optional[PaginationMeta] = None,
        links: Optional[Dict[str, str]] = None
    ) -> StandardResponse:
        """Build a success response"""
        meta = ResponseMeta(
            request_id=request_id,
            execution_time_ms=execution_time_ms,
            pagination=pagination
        )
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            meta=meta,
            links=links
        )
    
    @staticmethod
    def error(
        error: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> ErrorResponse:
        """Build an error response"""
        meta = ResponseMeta(request_id=request_id)
        
        return ErrorResponse(
            error=error,
            message=message,
            details=details,
            meta=meta,
            trace_id=trace_id
        )
    
    @staticmethod
    def validation_error(
        message: str,
        validation_errors: List[Dict[str, Any]],
        request_id: Optional[str] = None
    ) -> ValidationErrorResponse:
        """Build a validation error response"""
        meta = ResponseMeta(request_id=request_id)
        
        return ValidationErrorResponse(
            error="validation_error",
            message=message,
            validation_errors=validation_errors,
            meta=meta
        )
    
    @staticmethod
    def paginated_list(
        data: List[Any],
        current_page: int,
        page_size: int,
        total_items: int,
        message: Optional[str] = None,
        request_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None
    ) -> ListResponse:
        """Build a paginated list response"""
        total_pages = (total_items + page_size - 1) // page_size
        has_next = current_page < total_pages
        has_previous = current_page > 1
        
        pagination = PaginationMeta(
            current_page=current_page,
            total_pages=total_pages,
            page_size=page_size,
            total_items=total_items,
            has_next=has_next,
            has_previous=has_previous
        )
        
        meta = ResponseMeta(
            request_id=request_id,
            execution_time_ms=execution_time_ms,
            pagination=pagination
        )
        
        return ListResponse(
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            meta=meta
        )