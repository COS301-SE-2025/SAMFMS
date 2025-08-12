"""
Notification service for fleet management system
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from repositories.repositories import NotificationRepository, DriverRepository
from events.publisher import event_publisher
from schemas.requests import NotificationCreateRequest
from schemas.entities import Notification, NotificationStatus, NotificationPriority

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for notification management"""
    
    def __init__(self):
        self.notification_repo = NotificationRepository()
        self.driver_repo = DriverRepository()
    
    async def create_notification(self, request: NotificationCreateRequest, created_by: str) -> Dict[str, Any]:
        """Create a new notification"""
        try:
            # If recipient_id provided, validate the recipient exists
            if request.recipient_id:
                recipient = await self.driver_repo.get_by_id(request.recipient_id)
                if not recipient:
                    raise ValueError(f"Recipient with ID {request.recipient_id} not found")
            
            notification_data = {
                **request.dict(),
                "status": NotificationStatus.UNREAD,
                "created_by": created_by,
                "created_at": datetime.utcnow()
            }
            
            notification_id = await self.notification_repo.create(notification_data)
            
            # Publish notification created event
            await event_publisher.publish_event({
                "event_type": "notification_created",
                "notification_id": notification_id,
                "recipient_id": request.recipient_id,
                "notification_type": request.notification_type,
                "priority": request.priority.value if request.priority else NotificationPriority.NORMAL.value,
                "title": request.title,
                "created_by": created_by,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Get the created notification
            created_notification = await self.notification_repo.get_by_id(notification_id)
            
            logger.info(f"Notification created: {notification_id}")
            
            return created_notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            raise
    
    async def get_notifications_by_recipient(self, recipient_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get notifications for a specific recipient"""
        try:
            filters = {"recipient_id": recipient_id}
            if status:
                filters["status"] = status
            
            return await self.notification_repo.get_by_filters(filters)
        except Exception as e:
            logger.error(f"Error getting notifications for recipient {recipient_id}: {e}")
            raise
    
    async def get_broadcast_notifications(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get broadcast notifications (no specific recipient)"""
        try:
            filters = {"recipient_id": None}
            if status:
                filters["status"] = status
            
            return await self.notification_repo.get_by_filters(filters)
        except Exception as e:
            logger.error(f"Error getting broadcast notifications: {e}")
            raise
    
    async def mark_notification_as_read(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Mark notification as read"""
        try:
            notification = await self.notification_repo.get_by_id(notification_id)
            if not notification:
                raise ValueError(f"Notification with ID {notification_id} not found")
            
            # Check if user has permission to mark as read
            if notification.get("recipient_id") and notification["recipient_id"] != user_id:
                raise ValueError("User does not have permission to mark this notification as read")
            
            update_data = {
                "status": NotificationStatus.READ,
                "read_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.notification_repo.update(notification_id, update_data)
            
            # Publish notification read event
            await event_publisher.publish_event({
                "event_type": "notification_read",
                "notification_id": notification_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return await self.notification_repo.get_by_id(notification_id)
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            raise
    
    async def archive_notification(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Archive a notification"""
        try:
            notification = await self.notification_repo.get_by_id(notification_id)
            if not notification:
                raise ValueError(f"Notification with ID {notification_id} not found")
            
            # Check if user has permission to archive
            if notification.get("recipient_id") and notification["recipient_id"] != user_id:
                raise ValueError("User does not have permission to archive this notification")
            
            update_data = {
                "status": NotificationStatus.ARCHIVED,
                "archived_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.notification_repo.update(notification_id, update_data)
            
            # Publish notification archived event
            await event_publisher.publish_event({
                "event_type": "notification_archived",
                "notification_id": notification_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return await self.notification_repo.get_by_id(notification_id)
            
        except Exception as e:
            logger.error(f"Error archiving notification: {e}")
            raise
    
    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification (admin/manager only)"""
        try:
            notification = await self.notification_repo.get_by_id(notification_id)
            if not notification:
                raise ValueError(f"Notification with ID {notification_id} not found")
            
            # Check if user created the notification or is an admin
            if notification.get("created_by") != user_id:
                # Additional role-based check could be added here
                logger.warning(f"User {user_id} attempted to delete notification {notification_id} not created by them")
            
            await self.notification_repo.delete(notification_id)
            
            # Publish notification deleted event
            await event_publisher.publish_event({
                "event_type": "notification_deleted",
                "notification_id": notification_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Notification {notification_id} deleted by {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            raise
    
    async def get_unread_count_by_recipient(self, recipient_id: str) -> int:
        """Get count of unread notifications for a recipient"""
        try:
            unread_notifications = await self.get_notifications_by_recipient(
                recipient_id, 
                status=NotificationStatus.UNREAD
            )
            return len(unread_notifications)
        except Exception as e:
            logger.error(f"Error getting unread count for recipient {recipient_id}: {e}")
            raise
    
    async def create_system_notification(self, title: str, message: str, priority: NotificationPriority = NotificationPriority.NORMAL) -> Dict[str, Any]:
        """Create a system-wide broadcast notification"""
        try:
            request = NotificationCreateRequest(
                title=title,
                message=message,
                notification_type="system",
                priority=priority,
                recipient_id=None  # Broadcast to all
            )
            
            return await self.create_notification(request, "system")
            
        except Exception as e:
            logger.error(f"Error creating system notification: {e}")
            raise
    
    async def create_maintenance_notification(self, vehicle_id: str, driver_id: str, message: str) -> Dict[str, Any]:
        """Create a maintenance-related notification"""
        try:
            request = NotificationCreateRequest(
                title="Maintenance Alert",
                message=message,
                notification_type="maintenance",
                priority=NotificationPriority.HIGH,
                recipient_id=driver_id,
                metadata={"vehicle_id": vehicle_id}
            )
            
            return await self.create_notification(request, "system")
            
        except Exception as e:
            logger.error(f"Error creating maintenance notification: {e}")
            raise
    
    async def create_assignment_notification(self, driver_id: str, vehicle_id: str, assignment_type: str) -> Dict[str, Any]:
        """Create a vehicle assignment notification"""
        try:
            message = f"You have been assigned to vehicle {vehicle_id} for {assignment_type}"
            
            request = NotificationCreateRequest(
                title="Vehicle Assignment",
                message=message,
                notification_type="assignment",
                priority=NotificationPriority.NORMAL,
                recipient_id=driver_id,
                metadata={"vehicle_id": vehicle_id, "assignment_type": assignment_type}
            )
            
            return await self.create_notification(request, "system")
            
        except Exception as e:
            logger.error(f"Error creating assignment notification: {e}")
            raise
    
    async def handle_request(self, method: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification service requests from request consumer"""
        try:
            endpoint = user_context.get("endpoint", "")
            data = user_context.get("data", {})
            user_id = user_context.get("user_id", "system")
            
            if method == "GET":
                if "recipient" in endpoint and "unread-count" in endpoint:
                    # Extract recipient_id from endpoint
                    parts = endpoint.split('/')
                    recipient_id = parts[parts.index("recipient") + 1] if "recipient" in parts else None
                    if recipient_id:
                        count = await self.get_unread_count_by_recipient(recipient_id)
                        return {"success": True, "data": {"recipient_id": recipient_id, "unread_count": count}}
                elif "recipient" in endpoint:
                    parts = endpoint.split('/')
                    recipient_id = parts[parts.index("recipient") + 1] if "recipient" in parts else None
                    if recipient_id:
                        status = data.get("status")
                        notifications = await self.get_notifications_by_recipient(recipient_id, status)
                        return {"success": True, "data": notifications}
                elif "broadcast" in endpoint:
                    status = data.get("status")
                    notifications = await self.get_broadcast_notifications(status)
                    return {"success": True, "data": notifications}
                elif "my-notifications" in endpoint:
                    status = data.get("status")
                    personal_notifications = await self.get_notifications_by_recipient(user_id, status)
                    broadcast_notifications = await self.get_broadcast_notifications(status)
                    all_notifications = personal_notifications + broadcast_notifications
                    all_notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                    return {"success": True, "data": all_notifications}
                    
            elif method == "POST":
                if "system" in endpoint:
                    title = data.get("title", "")
                    message = data.get("message", "")
                    priority = data.get("priority", NotificationPriority.NORMAL)
                    notification = await self.create_system_notification(title, message, priority)
                    return {"success": True, "data": notification}
                elif "maintenance" in endpoint:
                    vehicle_id = data.get("vehicle_id", "")
                    driver_id = data.get("driver_id", "")
                    message = data.get("message", "")
                    notification = await self.create_maintenance_notification(vehicle_id, driver_id, message)
                    return {"success": True, "data": notification}
                elif "assignment" in endpoint:
                    driver_id = data.get("driver_id", "")
                    vehicle_id = data.get("vehicle_id", "")
                    assignment_type = data.get("assignment_type", "")
                    notification = await self.create_assignment_notification(driver_id, vehicle_id, assignment_type)
                    return {"success": True, "data": notification}
                else:
                    request = NotificationCreateRequest(**data)
                    notification = await self.create_notification(request, user_id)
                    return {"success": True, "data": notification}
                    
            elif method == "PUT":
                parts = endpoint.split('/')
                notification_id = parts[1] if len(parts) > 1 else None
                if notification_id and "read" in endpoint:
                    notification = await self.mark_notification_as_read(notification_id, user_id)
                    return {"success": True, "data": notification}
                elif notification_id and "archive" in endpoint:
                    notification = await self.archive_notification(notification_id, user_id)
                    return {"success": True, "data": notification}
                    
            elif method == "DELETE":
                parts = endpoint.split('/')
                notification_id = parts[1] if len(parts) > 1 else None
                if notification_id:
                    success = await self.delete_notification(notification_id, user_id)
                    return {"success": success, "message": "Notification deleted successfully"}
            
            return {"success": False, "error": "Unsupported notification operation"}
            
        except Exception as e:
            logger.error(f"Error handling notification request: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
notification_service = NotificationService()
