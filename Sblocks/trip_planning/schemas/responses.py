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

class VehiclePosition(BaseModel):
    """Current vehicle position data"""
    latitude: float = Field(..., description="Current latitude")
    longitude: float = Field(..., description="Current longitude")
    bearing: Optional[float] = Field(None, description="Vehicle heading in degrees (0-360)")
    speed: Optional[float] = Field(None, description="Current speed in km/h")
    accuracy: Optional[float] = Field(None, description="Position accuracy in meters")
    timestamp: datetime = Field(..., description="Position timestamp")

class RouteProgress(BaseModel):
    """Route progress information"""
    total_distance: float = Field(..., description="Total route distance in meters")
    remaining_distance: float = Field(..., description="Remaining distance in meters")
    completed_distance: float = Field(..., description="Completed distance in meters")
    progress_percentage: float = Field(..., description="Progress as percentage (0-100)")
    estimated_time_remaining: Optional[float] = Field(None, description="ETA in seconds")
    current_step_index: Optional[int] = Field(None, description="Current step in route")
    total_steps: Optional[int] = Field(None, description="Total number of steps")

class CurrentInstruction(BaseModel):
    """Current navigation instruction"""
    text: Optional[str] = Field(None, description="Instruction text")
    type: Optional[str] = Field(None, description="Instruction type")
    distance_to_instruction: Optional[float] = Field(None, description="Distance to next instruction in meters")
    road_name: Optional[str] = Field(None, description="Current road name")
    speed_limit: Optional[float] = Field(None, description="Current speed limit")

class LiveTrackingResponse(BaseModel):
    """Live tracking data for map display"""
    trip_id: str = Field(..., description="Trip identifier")
    vehicle_id: Optional[str] = Field(None, description="Vehicle identifier")
    driver_id: Optional[str] = Field(None, description="Driver identifier")
    trip_status: str = Field(..., description="Current trip status")
    
    # Vehicle position and movement
    current_position: VehiclePosition = Field(..., description="Current vehicle position")
    
    # Route information
    route_polyline: List[List[float]] = Field(..., description="Complete route as [lat, lon] coordinates")
    remaining_polyline: Optional[List[List[float]]] = Field(None, description="Remaining route from current position")
    route_bounds: Optional[Dict[str, Any]] = Field(None, description="Route bounding box")
    
    # Progress tracking
    progress: RouteProgress = Field(..., description="Route progress information")
    
    # Navigation
    current_instruction: Optional[CurrentInstruction] = Field(None, description="Current navigation instruction")
    
    # Trip details
    origin: Dict[str, Any] = Field(..., description="Trip origin information")
    destination: Dict[str, Any] = Field(..., description="Trip destination information")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled departure time")
    actual_start_time: Optional[datetime] = Field(None, description="Actual start time")
    
    # Simulation info
    is_simulated: bool = Field(default=False, description="Whether this is simulated data")
    last_updated: datetime = Field(..., description="Last update timestamp")
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


class DriverPingResponse(BaseModel):
    """Response from driver ping endpoint"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat() + 'Z'})
    
    status: str = Field(..., description="Status of ping processing")
    message: str = Field(..., description="Response message")
    ping_received_at: datetime = Field(..., description="When ping was received")
    next_ping_expected_at: datetime = Field(..., description="When next ping is expected")
    session_active: bool = Field(..., description="Whether ping session is active")
    violations_count: int = Field(default=0, description="Number of violations in current session")