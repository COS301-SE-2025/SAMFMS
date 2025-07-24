"""
Response schemas for Trip Planning service
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from .entities import (
    Trip, TripAnalytics, Notification, NotificationPreferences,
    TripConstraint, DriverAssignment
)


class ResponseBuilder:
    """Utility class for building standardized responses"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operation successful",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build a successful response"""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if data is not None:
            response["data"] = data
            
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    @staticmethod
    def error(
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ) -> Dict[str, Any]:
        """Build an error response"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status_code
        }
        
        if error_code:
            response["error_code"] = error_code
            
        if details:
            response["details"] = details
            
        return response
    
    @staticmethod
    def paginated(
        items: List[Any],
        total: int,
        skip: int,
        limit: int,
        message: str = "Data retrieved successfully"
    ) -> Dict[str, Any]:
        """Build a paginated response"""
        return ResponseBuilder.success(
            data=items,
            message=message,
            metadata={
                "pagination": {
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "count": len(items),
                    "has_more": skip + len(items) < total
                }
            }
        )


class TripResponse(BaseModel):
    """Response containing a single trip"""
    trip: Trip
    
    class Config:
        schema_extra = {
            "example": {
                "trip": {
                    "id": "trip_12345",
                    "name": "Delivery to Cape Town",
                    "status": "scheduled",
                    "scheduled_start_time": "2024-03-15T08:00:00Z",
                    "origin": {
                        "location": {"type": "Point", "coordinates": [18.4241, -33.9249]},
                        "name": "Warehouse"
                    },
                    "destination": {
                        "location": {"type": "Point", "coordinates": [18.4232, -33.9258]},
                        "name": "Customer Location"
                    }
                }
            }
        }


class TripListResponse(BaseModel):
    """Response containing a list of trips"""
    trips: List[Trip]
    total: int
    skip: int
    limit: int
    
    class Config:
        schema_extra = {
            "example": {
                "trips": [],
                "total": 100,
                "skip": 0,
                "limit": 50
            }
        }


class DriverAvailabilityResponse(BaseModel):
    """Response for driver availability check"""
    driver_id: str
    is_available: bool
    conflicting_trips: Optional[List[str]] = None
    next_available: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "driver_id": "driver_123",
                "is_available": False,
                "conflicting_trips": ["trip_456"],
                "next_available": "2024-03-15T14:00:00Z"
            }
        }


class RouteOptimizationResponse(BaseModel):
    """Response for route optimization"""
    trip_id: str
    original_duration: int = Field(..., description="Original duration in minutes")
    optimized_duration: int = Field(..., description="Optimized duration in minutes")
    original_distance: float = Field(..., description="Original distance in km")
    optimized_distance: float = Field(..., description="Optimized distance in km")
    time_saved: int = Field(..., description="Time saved in minutes")
    distance_saved: float = Field(..., description="Distance saved in km")
    optimized_route: List[Dict[str, Any]] = Field(..., description="Optimized route waypoints")
    
    class Config:
        schema_extra = {
            "example": {
                "trip_id": "trip_123",
                "original_duration": 120,
                "optimized_duration": 95,
                "original_distance": 85.5,
                "optimized_distance": 78.2,
                "time_saved": 25,
                "distance_saved": 7.3,
                "optimized_route": []
            }
        }


class TripAnalyticsResponse(BaseModel):
    """Response for trip analytics"""
    period_start: datetime
    period_end: datetime
    total_trips: int
    completed_trips: int
    cancelled_trips: int
    
    # Performance metrics
    average_duration: Optional[float] = Field(None, description="Average trip duration in minutes")
    average_distance: Optional[float] = Field(None, description="Average trip distance in km")
    total_distance: Optional[float] = Field(None, description="Total distance traveled in km")
    
    # Efficiency metrics
    on_time_percentage: Optional[float] = Field(None, description="Percentage of on-time trips")
    average_delay: Optional[float] = Field(None, description="Average delay in minutes")
    fuel_efficiency: Optional[float] = Field(None, description="Average fuel consumption per km")
    
    # Cost metrics
    total_cost: Optional[float] = None
    average_cost_per_trip: Optional[float] = None
    cost_per_km: Optional[float] = None
    
    # Detailed data
    by_period: Optional[List[Dict[str, Any]]] = Field(None, description="Breakdown by time period")
    by_driver: Optional[List[Dict[str, Any]]] = Field(None, description="Breakdown by driver")
    by_vehicle: Optional[List[Dict[str, Any]]] = Field(None, description="Breakdown by vehicle")
    
    class Config:
        schema_extra = {
            "example": {
                "period_start": "2024-03-01T00:00:00Z",
                "period_end": "2024-03-31T23:59:59Z",
                "total_trips": 250,
                "completed_trips": 235,
                "cancelled_trips": 15,
                "average_duration": 87.5,
                "average_distance": 45.2,
                "on_time_percentage": 92.5
            }
        }


class DriverPerformanceResponse(BaseModel):
    """Response for driver performance analytics"""
    driver_id: str
    driver_name: Optional[str] = None
    
    # Trip statistics
    total_trips: int
    completed_trips: int
    cancelled_trips: int
    
    # Performance metrics
    on_time_rate: float = Field(..., description="Percentage of on-time trips")
    average_trip_duration: Optional[float] = Field(None, description="Average trip duration in minutes")
    total_distance: Optional[float] = Field(None, description="Total distance driven in km")
    
    # Efficiency metrics
    fuel_efficiency: Optional[float] = Field(None, description="Fuel efficiency in L/100km")
    safety_score: Optional[float] = Field(None, description="Safety score (0-100)")
    
    # Rating
    average_rating: Optional[float] = Field(None, description="Average customer rating")
    
    class Config:
        schema_extra = {
            "example": {
                "driver_id": "driver_123",
                "driver_name": "John Smith",
                "total_trips": 45,
                "completed_trips": 43,
                "cancelled_trips": 2,
                "on_time_rate": 95.5,
                "average_trip_duration": 82.3,
                "total_distance": 2156.7
            }
        }


class NotificationResponse(BaseModel):
    """Response containing a notification"""
    notification: Notification
    
    class Config:
        schema_extra = {
            "example": {
                "notification": {
                    "id": "notif_123",
                    "type": "trip_started",
                    "title": "Trip Started",
                    "message": "Your trip to Cape Town has started",
                    "is_read": False,
                    "sent_at": "2024-03-15T08:00:00Z"
                }
            }
        }


class NotificationListResponse(BaseModel):
    """Response containing a list of notifications"""
    notifications: List[Notification]
    unread_count: int
    total: int
    
    class Config:
        schema_extra = {
            "example": {
                "notifications": [],
                "unread_count": 5,
                "total": 25
            }
        }


class ConstraintResponse(BaseModel):
    """Response containing a trip constraint"""
    constraint: TripConstraint
    
    class Config:
        schema_extra = {
            "example": {
                "constraint": {
                    "id": "constraint_123",
                    "trip_id": "trip_456",
                    "type": "avoid_tolls",
                    "priority": 5,
                    "is_active": True
                }
            }
        }


class AssignmentResponse(BaseModel):
    """Response for driver assignment"""
    assignment: DriverAssignment
    driver_name: Optional[str] = None
    vehicle_info: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "assignment": {
                    "trip_id": "trip_123",
                    "driver_id": "driver_456",
                    "vehicle_id": "vehicle_789",
                    "assigned_at": "2024-03-15T10:00:00Z"
                },
                "driver_name": "John Smith",
                "vehicle_info": {
                    "make": "Ford",
                    "model": "Transit",
                    "license_plate": "ABC123"
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    service: str
    version: str
    components: Dict[str, str]
    metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-03-15T10:00:00Z",
                "service": "trip_planning",
                "version": "1.0.0",
                "components": {
                    "database": "healthy",
                    "events": "healthy"
                }
            }
        }
