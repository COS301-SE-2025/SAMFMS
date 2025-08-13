"""
Notifications API routes for the Trip Planning service
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from api.dependencies import get_current_user_secure
from services.notification_service import notification_service
from schemas.requests import NotificationRequest, UpdateNotificationPreferencesRequest
from schemas.responses import ResponseBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def get_notifications(
    unread_only: bool = Query(False, description="Get only unread notifications"),
    limit: int = Query(50, description="Number of notifications to retrieve", ge=1, le=100),
    skip: int = Query(0, description="Number of notifications to skip", ge=0),
    current_user: dict = Depends(get_current_user_secure)
):
    """Get notifications for the current user"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in context")

        notifications, total = await notification_service.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit,
            skip=skip
        )

        # Convert notifications to dict format
        notifications_data = []
        for notification in notifications:
            notification_dict = {
                "id": notification.id if hasattr(notification, 'id') else str(notification._id),
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "time": notification.sent_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(notification.sent_at, 'strftime') else str(notification.sent_at),
                "read": notification.is_read,
                "trip_id": getattr(notification, 'trip_id', None),
                "driver_id": getattr(notification, 'driver_id', None),
                "data": getattr(notification, 'data', {})
            }
            notifications_data.append(notification_dict)

        unread_count = await notification_service.get_unread_count(user_id)

        return ResponseBuilder.success(
            data={
                "notifications": notifications_data,
                "total": total,
                "unread_count": unread_count
            },
            message="Notifications retrieved successfully"
        ).model_dump()

    except Exception as e:
        logger.error(f"Error retrieving notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notifications: {str(e)}")


@router.post("/")
async def send_notification(
    notification_request: NotificationRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Send notification to specified users (admin/fleet_manager only)"""
    try:
        user_role = current_user.get("role")
        if user_role not in ["admin", "fleet_manager"]:
            raise HTTPException(
                status_code=403, 
                detail="Insufficient permissions to send notifications"
            )

        notifications = await notification_service.send_notification(notification_request)

        return ResponseBuilder.success(
            data={
                "sent_count": len(notifications),
                "notification_ids": [str(n._id) if hasattr(n, '_id') else n.id for n in notifications]
            },
            message="Notifications sent successfully"
        ).model_dump()

    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notifications: {str(e)}")


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user_secure)
):
    """Mark a notification as read"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in context")

        result = await notification_service.mark_notification_read(notification_id, user_id)

        return ResponseBuilder.success(
            data={"marked_read": result},
            message="Notification marked as read" if result else "Notification not found or already read"
        ).model_dump()

    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@router.get("/unread/count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user_secure)
):
    """Get count of unread notifications for the current user"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in context")

        unread_count = await notification_service.get_unread_count(user_id)

        return ResponseBuilder.success(
            data={"unread_count": unread_count},
            message="Unread notification count retrieved successfully"
        ).model_dump()

    except Exception as e:
        logger.error(f"Error retrieving unread count: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve unread count: {str(e)}")


@router.get("/preferences")
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user_secure)
):
    """Get notification preferences for the current user"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in context")

        preferences = await notification_service.get_user_preferences(user_id)

        return ResponseBuilder.success(
            data=preferences.model_dump() if preferences else None,
            message="Notification preferences retrieved successfully"
        ).model_dump()

    except Exception as e:
        logger.error(f"Error retrieving notification preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notification preferences: {str(e)}")


@router.put("/preferences")
async def update_notification_preferences(
    preferences_request: UpdateNotificationPreferencesRequest,
    current_user: dict = Depends(get_current_user_secure)
):
    """Update notification preferences for the current user"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in context")

        preferences = await notification_service.update_user_preferences(user_id, preferences_request)

        return ResponseBuilder.success(
            data=preferences.model_dump(),
            message="Notification preferences updated successfully"
        ).model_dump()

    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update notification preferences: {str(e)}")
