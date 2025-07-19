
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class PaginationMeta(BaseModel):
    
    current_page: int = Field(..., description="Current page number")
    total_pages: int = Field(..., description="Total number of pages")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class ResponseMeta(BaseModel):
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    version: str = Field(default="2.0.0", description="API version")
    pagination: Optional[PaginationMeta] = Field(None, description="Pagination information")


class StandardResponse(BaseModel):
    
    status: ResponseStatus = Field(..., description="Response status")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")
    links: Optional[Dict[str, str]] = Field(None, description="Related links")


class ErrorResponse(BaseModel):
    
    status: ResponseStatus = Field(default=ResponseStatus.ERROR, description="Response status")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")
    trace_id: Optional[str] = Field(None, description="Trace ID for debugging")


class ValidationErrorResponse(ErrorResponse):
    
    validation_errors: List[Dict[str, Any]] = Field(..., description="List of validation errors")


class SuccessResponse(StandardResponse):
    
    status: ResponseStatus = Field(default=ResponseStatus.SUCCESS, description="Response status")


class ListResponse(SuccessResponse):
    
    data: List[Any] = Field(..., description="List of items")
    
    @property
    def total_items(self) -> int:
        
        return self.meta.pagination.total_items if self.meta.pagination else len(self.data)


class HealthCheckResponse(BaseModel):
    
    status: str = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    components: Dict[str, str] = Field(..., description="Component health status")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")


class EventInfoResponse(BaseModel):
    
    event_system: Dict[str, Any] = Field(..., description="Event system status and configuration")



class ResponseBuilder:
    
    
    @staticmethod
    def success(
        data: Any = None, 
        message: Optional[str] = None,
        request_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        pagination: Optional[PaginationMeta] = None
    ) -> StandardResponse:
        
        meta = ResponseMeta(
            request_id=request_id,
            execution_time_ms=execution_time_ms,
            pagination=pagination
        )
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            data=data,
            message=message,
            meta=meta
        )
    
    @staticmethod
    def error(
        error: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> ErrorResponse:
        
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
        
        meta = ResponseMeta(request_id=request_id)
        
        return ValidationErrorResponse(
            error="ValidationError",
            message=message,
            validation_errors=validation_errors,
            meta=meta
        )
    
    @staticmethod
    def paginated_list(
        items: List[Any],
        total_items: int,
        current_page: int,
        page_size: int,
        message: Optional[str] = None,
        request_id: Optional[str] = None,
        execution_time_ms: Optional[float] = None
    ) -> ListResponse:
        
        total_pages = (total_items + page_size - 1) // page_size
        
        pagination = PaginationMeta(
            current_page=current_page,
            total_pages=total_pages,
            page_size=page_size,
            total_items=total_items,
            has_next=current_page < total_pages,
            has_previous=current_page > 1
        )
        
        meta = ResponseMeta(
            request_id=request_id,
            execution_time_ms=execution_time_ms,
            pagination=pagination
        )
        
        return ListResponse(
            data=items,
            message=message,
            meta=meta
        )
