"""
Notification API Routes
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query

from ..dependencies import (
    get_authenticated_user,
    require_permissions,
    validate_object_id,
    get_request_timer
)
from schemas.responses import ResponseBuilder
from services.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["maintenance_notifications"])


@router.get("/pending")
async def get_pending_notifications(
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.notifications.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get notifications that need to be sent"""
    try:
        notifications = await notification_service.get_pending_notifications()
        
        return ResponseBuilder.success(
            data=notifications,
            message="Pending notifications retrieved successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "total": len(notifications)
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving pending notifications: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.get("/user/{user_id}")
async def get_user_notifications(
    user_id: str = Depends(validate_object_id),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.notifications.read"])),
    timer: object = Depends(get_request_timer)
):
    """Get notifications for a specific user"""
    try:
        notifications = await notification_service.get_user_notifications(user_id, unread_only)
        
        message = f"Notifications for user {user_id} retrieved successfully"
        if unread_only:
            message = f"Unread notifications for user {user_id} retrieved successfully"
            
        return ResponseBuilder.success(
            data=notifications,
            message=message,
            request_id=timer.request_id,
            execution_time=timer.elapsed,
            metadata={
                "total": len(notifications),
                "user_id": user_id,
                "unread_only": unread_only
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving notifications for user {user_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.post("/process")
async def process_pending_notifications(
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.notifications.send"])),
    timer: object = Depends(get_request_timer)
):
    """Process and send pending notifications"""
    try:
        sent_count = await notification_service.process_pending_notifications()
        
        return ResponseBuilder.success(
            data={"sent_count": sent_count},
            message=f"Processed and sent {sent_count} notifications",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error processing pending notifications: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str = Depends(validate_object_id),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.notifications.update"])),
    timer: object = Depends(get_request_timer)
):
    """Mark a notification as read"""
    try:
        success = await notification_service.mark_notification_read(notification_id)
        
        if not success:
            return ResponseBuilder.error(
                message="Notification not found",
                status_code=404,
                request_id=timer.request_id,
                execution_time=timer.elapsed
            )
            
        return ResponseBuilder.success(
            message="Notification marked as read",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )


@router.put("/{notification_id}/send")
async def send_notification(
    notification_id: str = Depends(validate_object_id),
    user: dict = Depends(get_authenticated_user),
    _: None = Depends(require_permissions(["maintenance.notifications.send"])),
    timer: object = Depends(get_request_timer)
):
    """Manually send a specific notification"""
    try:
        success = await notification_service.send_notification(notification_id)
        
        if not success:
            return ResponseBuilder.error(
                message="Notification not found",
                status_code=404,
                request_id=timer.request_id,
                execution_time=timer.elapsed
            )
            
        return ResponseBuilder.success(
            message="Notification sent successfully",
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
        
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {e}")
        return ResponseBuilder.error(
            message="Internal server error",
            status_code=500,
            request_id=timer.request_id,
            execution_time=timer.elapsed
        )
