"""
Driver phone ping API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any
import logging
from datetime import datetime

from services.driver_ping_service import driver_ping_service
from services.trip_service import trip_service
from api.dependencies import get_current_user, require_permission, get_request_id, RequestTimer
from schemas.requests import DriverPingRequest
from schemas.responses import DriverPingResponse, StandardResponse, ResponseStatus
from schemas.entities import TripStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/driver/ping", response_model=StandardResponse)
async def receive_driver_ping(
    request: Request,
    ping_data: DriverPingRequest,
    current_user = Depends(require_permission("trips:ping"))
):
    """
    Receive driver phone ping during trip
    
    This endpoint is pinged by the driver's phone while on a trip to monitor phone usage.
    If pings are not received every 30 seconds, a phone usage violation will be created.
    """
    request_id = get_request_id(request)
    timer = RequestTimer()
    
    logger.info(f"[DriverPingAPI] Processing ping for trip {ping_data.trip_id}")
    
    try:
        # Validate trip exists and is active
        trip = await trip_service.get_trip_by_id(ping_data.trip_id)
        if not trip:
            raise HTTPException(
                status_code=404,
                detail=f"Trip {ping_data.trip_id} not found"
            )
        
        # Check if trip is in a state where pings should be monitored
        if trip.status not in [TripStatus.IN_PROGRESS]:
            return StandardResponse(
                status=ResponseStatus.WARNING,
                data=DriverPingResponse(
                    status="trip_not_active",
                    message=f"Trip is not in progress (status: {trip.status}). Ping ignored.",
                    ping_received_at=ping_data.timestamp,
                    next_ping_expected_at=ping_data.timestamp,
                    session_active=False,
                    violations_count=0
                ),
                message="Trip is not in active state for ping monitoring"
            )
        
        # Validate driver assignment matches current user (optional security check)
        if trip.driver_assignment and trip.driver_assignment != current_user.get("user_id"):
            logger.warning(f"[DriverPingAPI] Driver mismatch: trip assigned to {trip.driver_assignment}, ping from {current_user.get('user_id')}")
        
        # Process the ping
        result = await driver_ping_service.process_ping(
            trip_id=ping_data.trip_id,
            location=ping_data.location,
            ping_time=ping_data.timestamp
        )
        
        if result["status"] == "error":
            return StandardResponse(
                status=ResponseStatus.ERROR,
                data=None,
                message=result["message"]
            )
        
        # Build response
        ping_response = DriverPingResponse(
            status=result["status"],
            message=result["message"],
            ping_received_at=result["ping_received_at"],
            next_ping_expected_at=result["next_ping_expected_at"],
            session_active=result["session_active"],
            violations_count=result["violations_count"]
        )
        
        logger.info(f"[DriverPingAPI] Successfully processed ping for trip {ping_data.trip_id}")
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            data=ping_response,
            message="Ping processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DriverPingAPI] Failed to process ping: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process driver ping: {str(e)}"
        )


@router.get("/driver/ping/violations/{trip_id}", response_model=StandardResponse)
async def get_trip_violations(
    request: Request,
    trip_id: str,
    current_user = Depends(require_permission("trips:read"))
):
    """
    Get all phone usage violations for a trip
    """
    request_id = get_request_id(request)
    timer = RequestTimer()
    
    logger.info(f"[DriverPingAPI] Getting violations for trip {trip_id}")
    
    try:
        # Validate trip exists
        trip = await trip_service.get_trip_by_id(trip_id)
        if not trip:
            raise HTTPException(
                status_code=404,
                detail=f"Trip {trip_id} not found"
            )
        
        # Get violations
        violations = await driver_ping_service.get_trip_violations(trip_id)
        
        # Convert to dict for response
        violations_data = [violation.dict() for violation in violations]
        
        logger.info(f"[DriverPingAPI] Retrieved {len(violations)} violations for trip {trip_id}")
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            data={
                "trip_id": trip_id,
                "violations": violations_data,
                "total_violations": len(violations)
            },
            message=f"Retrieved {len(violations)} violations for trip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DriverPingAPI] Failed to get violations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trip violations: {str(e)}"
        )


@router.get("/driver/ping/session/{trip_id}", response_model=StandardResponse)
async def get_ping_session_status(
    request: Request,
    trip_id: str,
    current_user = Depends(require_permission("trips:read"))
):
    """
    Get current ping session status for a trip
    """
    request_id = get_request_id(request)
    timer = RequestTimer()
    
    logger.info(f"[DriverPingAPI] Getting ping session status for trip {trip_id}")
    
    try:
        # Get active session
        session = await driver_ping_service._get_active_session(trip_id)
        
        if not session:
            return StandardResponse(
                status=ResponseStatus.SUCCESS,
                data={
                    "trip_id": trip_id,
                    "session_active": False,
                    "message": "No active ping session found"
                },
                message="No active ping session for this trip"
            )
        
        session_data = session.dict()
        session_data["session_active"] = session.is_active
        
        logger.info(f"[DriverPingAPI] Retrieved ping session status for trip {trip_id}")
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            data=session_data,
            message="Ping session status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"[DriverPingAPI] Failed to get session status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ping session status: {str(e)}"
        )