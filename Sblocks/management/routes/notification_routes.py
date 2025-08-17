"""
API routes for notification management
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query

from services.notification_service import notification_service
from schemas.requests import NotificationCreateRequest
from schemas.entities import NotificationPriority

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/", response_model=Dict[str, Any])
async def create_notification(
    request: NotificationCreateRequest
):
    """Create a new notification"""
    try:
        result = await notification_service.create_notification(request, "system")
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recipient/{recipient_id}", response_model=Dict[str, Any])
async def get_notifications_by_recipient(
    recipient_id: str,
    status: Optional[str] = Query(None)
):
    """Get notifications for a specific recipient"""
    try:
        notifications = await notification_service.get_notifications_by_recipient(recipient_id, status)
        return {"success": True, "data": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/broadcast", response_model=Dict[str, Any])
async def get_broadcast_notifications(
    status: Optional[str] = Query(None)
):
    """Get broadcast notifications"""
    try:
        notifications = await notification_service.get_broadcast_notifications(status)
        return {"success": True, "data": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{notification_id}/read", response_model=Dict[str, Any])
async def mark_notification_as_read(
    notification_id: str
):
    """Mark notification as read"""
    try:
        result = await notification_service.mark_notification_as_read(
            notification_id, "system"
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{notification_id}/archive", response_model=Dict[str, Any])
async def archive_notification(
    notification_id: str
):
    """Archive a notification"""
    try:
        result = await notification_service.archive_notification(
            notification_id, "system"
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{notification_id}", response_model=Dict[str, Any])
async def delete_notification(
    notification_id: str
):
    """Delete a notification"""
    try:
        success = await notification_service.delete_notification(
            notification_id, "system"
        )
        return {"success": success, "message": "Notification deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recipient/{recipient_id}/unread-count", response_model=Dict[str, Any])
async def get_unread_count(
    recipient_id: str
):
    """Get unread notification count for a recipient"""
    try:
        count = await notification_service.get_unread_count_by_recipient(recipient_id)
        return {"success": True, "data": {"recipient_id": recipient_id, "unread_count": count}}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/system", response_model=Dict[str, Any])
async def create_system_notification(
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.NORMAL
):
    """Create a system-wide broadcast notification"""
    try:
        result = await notification_service.create_system_notification(title, message, priority)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/maintenance", response_model=Dict[str, Any])
async def create_maintenance_notification(
    vehicle_id: str,
    driver_id: str,
    message: str
):
    """Create a maintenance-related notification"""
    try:
        result = await notification_service.create_maintenance_notification(
            vehicle_id, driver_id, message
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/assignment", response_model=Dict[str, Any])
async def create_assignment_notification(
    driver_id: str,
    vehicle_id: str,
    assignment_type: str
):
    """Create a vehicle assignment notification"""
    try:
        result = await notification_service.create_assignment_notification(
            driver_id, vehicle_id, assignment_type
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/my-notifications", response_model=Dict[str, Any])
async def get_my_notifications(
    status: Optional[str] = Query(None)
):
    """Get notifications for the current user"""
    try:
        # For now, return empty since we don't have user context
        # In production, this would get user_id from authentication
        return {"success": True, "data": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
