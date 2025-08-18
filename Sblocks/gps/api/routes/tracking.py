"""
Vehicle tracking session API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import Optional, List
import logging

from services.location_service import location_service
from api.dependencies import get_current_user, require_permission, get_request_id, RequestTimer
from schemas.responses import ResponseBuilder
from schemas.requests import TrackingSessionRequest
from api.exception_handlers import BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/tracking/sessions")
async def start_tracking_session(
    request: Request,
    session_data: TrackingSessionRequest,
    current_user = Depends(require_permission("gps:write"))
):
    """Start a new tracking session for a vehicle"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            user_id = current_user.get('user_id')
            
            session = await location_service.start_tracking_session(
                vehicle_id=session_data.vehicle_id,
                user_id=user_id
            )
            
            logger.info(f"Started tracking session for vehicle {session_data.vehicle_id}")
            
            return ResponseBuilder.success(
                data=session.model_dump(),
                message="Tracking session started successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error starting tracking session: {e}")
            raise BusinessLogicError("Failed to start tracking session")


@router.delete("/tracking/sessions/{session_id}")
async def end_tracking_session(
    request: Request,
    session_id: str,
    current_user = Depends(require_permission("gps:write"))
):
    """End a tracking session"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            success = await location_service.end_tracking_session(session_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Tracking session not found or already ended")
            
            return ResponseBuilder.success(
                data={"session_id": session_id, "ended": True},
                message="Tracking session ended successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error ending tracking session: {e}")
            raise BusinessLogicError("Failed to end tracking session")


@router.get("/tracking/sessions")
async def get_active_tracking_sessions(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    current_user = Depends(require_permission("gps:read"))
):
    """Get active tracking sessions"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            # If user_id not provided and user doesn't have admin permission, filter by their user_id
            if not user_id and not current_user.get('is_admin', False):
                user_id = current_user.get('user_id')
            
            sessions = await location_service.get_active_tracking_sessions(user_id)
            
            return ResponseBuilder.success(
                data=[session.model_dump() for session in sessions],
                message=f"Retrieved {len(sessions)} active tracking sessions",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            ).model_dump()
            
        except Exception as e:
            logger.error(f"Error getting active tracking sessions: {e}")
            raise BusinessLogicError("Failed to retrieve tracking sessions")
