"""
Notification API Routes
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request, Path

from api.dependencies import (
    get_current_user,
    require_permission,
    validate_object_id,
    RequestTimer,
    get_request_id
)
from schemas.responses import ResponseBuilder
from services.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/maintenance/notifications", tags=["maintenance_notifications"])


@router.get("/pending")
async def get_pending_notifications(
    request: Request,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_permission("maintenance.notifications.read"))
):
    """Get notifications that need to be sent"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            notifications = await notification_service.get_pending_notifications()
            
            return ResponseBuilder.success(
                data=notifications,
                message="Pending notifications retrieved successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms,
                metadata={
                    "total": len(notifications)
                }
            )
            
        except Exception as e:
            logger.error(f"Error retrieving pending notifications: {e}")
            return ResponseBuilder.error(
                message="Internal server error",
                status_code=500,
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )


@router.get("/user/{user_id}")
async def get_user_notifications(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    user: dict = Depends(get_current_user),
    _: None = Depends(require_permission("maintenance.notifications.read"))
):
    """Get notifications for a specific user"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            validate_object_id(user_id, "user ID")
            notifications = await notification_service.get_user_notifications(user_id, unread_only)
            
            message = f"Notifications for user {user_id} retrieved successfully"
            if unread_only:
                message = f"Unread notifications for user {user_id} retrieved successfully"
                
            return ResponseBuilder.success(
                data=notifications,
                message=message,
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms,
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
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )


@router.post("/process")
async def process_pending_notifications(
    request: Request,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_permission("maintenance.notifications.send"))
):
    """Process and send pending notifications"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            sent_count = await notification_service.process_pending_notifications()
            
            return ResponseBuilder.success(
                data={"sent_count": sent_count},
                message=f"Processed and sent {sent_count} notifications",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error processing pending notifications: {e}")
            return ResponseBuilder.error(
                message="Internal server error",
                status_code=500,
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )


@router.put("/{notification_id}/read")
async def mark_notification_read(
    request: Request,
    notification_id: str = Path(..., description="Notification ID"),
    user: dict = Depends(get_current_user),
    _: None = Depends(require_permission("maintenance.notifications.update"))
):
    """Mark a notification as read"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            validate_object_id(notification_id, "notification ID")
            success = await notification_service.mark_notification_read(notification_id)
            
            if not success:
                return ResponseBuilder.error(
                    message="Notification not found",
                    status_code=404,
                    request_id=request_id,
                    execution_time_ms=timer.execution_time_ms
                )
                
            return ResponseBuilder.success(
                message="Notification marked as read",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            return ResponseBuilder.error(
                message="Internal server error",
                status_code=500,
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )


@router.put("/{notification_id}/send")
async def send_notification(
    request: Request,
    notification_id: str = Path(..., description="Notification ID"),
    user: dict = Depends(get_current_user),
    _: None = Depends(require_permission("maintenance.notifications.send"))
):
    """Manually send a specific notification"""
    request_id = await get_request_id(request)
    
    with RequestTimer() as timer:
        try:
            validate_object_id(notification_id, "notification ID")
            success = await notification_service.send_notification(notification_id)
            
            if not success:
                return ResponseBuilder.error(
                    message="Notification not found",
                    status_code=404,
                    request_id=request_id,
                    execution_time_ms=timer.execution_time_ms
                )
                
            return ResponseBuilder.success(
                message="Notification sent successfully",
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error sending notification {notification_id}: {e}")
            return ResponseBuilder.error(
                message="Internal server error",
                status_code=500,
                request_id=request_id,
                execution_time_ms=timer.execution_time_ms
            )
