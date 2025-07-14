"""
Notification API Routes
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from schemas.responses import (
    DataResponse,
    ListResponse,
    ErrorResponse
)
from services.notification_service import notification_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/maintenance/notifications", tags=["maintenance_notifications"])


@router.get("/pending", response_model=ListResponse)
async def get_pending_notifications():
    """Get notifications that need to be sent"""
    try:
        notifications = await notification_service.get_pending_notifications()
        
        return ListResponse(
            success=True,
            message="Pending notifications retrieved successfully",
            data=notifications,
            total=len(notifications)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving pending notifications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}", response_model=ListResponse)
async def get_user_notifications(
    user_id: str,
    unread_only: bool = Query(False, description="Return only unread notifications")
):
    """Get notifications for a specific user"""
    try:
        notifications = await notification_service.get_user_notifications(user_id, unread_only)
        
        message = f"Notifications for user {user_id} retrieved successfully"
        if unread_only:
            message = f"Unread notifications for user {user_id} retrieved successfully"
            
        return ListResponse(
            success=True,
            message=message,
            data=notifications,
            total=len(notifications)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving notifications for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process", response_model=DataResponse)
async def process_pending_notifications():
    """Process and send pending notifications"""
    try:
        sent_count = await notification_service.process_pending_notifications()
        
        return DataResponse(
            success=True,
            message=f"Processed and sent {sent_count} notifications",
            data={"sent_count": sent_count}
        )
        
    except Exception as e:
        logger.error(f"Error processing pending notifications: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{notification_id}/read", response_model=DataResponse)
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    try:
        success = await notification_service.mark_notification_read(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        return DataResponse(
            success=True,
            message="Notification marked as read"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{notification_id}/send", response_model=DataResponse)
async def send_notification(notification_id: str):
    """Manually send a specific notification"""
    try:
        success = await notification_service.send_notification(notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        return DataResponse(
            success=True,
            message="Notification sent successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
