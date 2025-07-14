"""
Response schemas for Maintenance Service
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response schema"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseResponse):
    """Error response schema"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DataResponse(BaseResponse):
    """Response with data payload"""
    data: Optional[Dict[str, Any]] = None


class ListResponse(BaseResponse):
    """Response for list operations"""
    data: List[Dict[str, Any]] = []
    total: int = 0
    skip: int = 0
    limit: int = 100
    has_more: bool = False


class AnalyticsResponse(BaseResponse):
    """Response for analytics data"""
    data: Dict[str, Any] = {}
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    cache_info: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    service: str = "maintenance"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    dependencies: Optional[Dict[str, str]] = None


class ServiceStatusResponse(BaseModel):
    """Service status response"""
    service_name: str = "maintenance"
    status: str
    uptime: Optional[str] = None
    connections: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
