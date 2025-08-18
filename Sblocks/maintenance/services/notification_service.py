"""
Notification Service for Maintenance
Handles notification creation and delivery for maintenance events
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date

from repositories import MaintenanceNotificationsRepository
from schemas.entities import MaintenancePriority

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for maintenance notifications"""
    
    def __init__(self):
        self.repository = MaintenanceNotificationsRepository()
        
    async def create_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notification"""
        try:
            # Validate required fields
            required_fields = ["title", "message", "notification_type"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Required field '{field}' is missing")
            
            # Set default values
            if "priority" not in data:
                data["priority"] = MaintenancePriority.MEDIUM
            if "is_sent" not in data:
                data["is_sent"] = False
            if "is_read" not in data:
                data["is_read"] = False
            if "recipient_user_ids" not in data:
                data["recipient_user_ids"] = []
            if "recipient_roles" not in data:
                data["recipient_roles"] = []
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
                
            # Parse scheduled send time if provided
            if "scheduled_send_time" in data and isinstance(data["scheduled_send_time"], str):
                data["scheduled_send_time"] = datetime.fromisoformat(data["scheduled_send_time"].replace("Z", "+00:00"))
                
            notification = await self.repository.create(data)
            logger.info(f"Created notification {notification['id']}: {data['title']}")
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            raise
            
    async def send_notification(self, notification_id: str) -> bool:
        """Mark notification as sent"""
        try:
            await self.repository.mark_as_sent(notification_id)
            logger.info(f"Marked notification {notification_id} as sent")
            return True
        except Exception as e:
            logger.error(f"Error sending notification {notification_id}: {e}")
            raise
            
    async def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get notifications that need to be sent"""
        try:
            return await self.repository.get_pending_notifications()
        except Exception as e:
            logger.error(f"Error fetching pending notifications: {e}")
            raise
            
    async def get_user_notifications(self, user_id: str, 
                                   unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for a specific user"""
        try:
            return await self.repository.get_user_notifications(user_id, unread_only)
        except Exception as e:
            logger.error(f"Error fetching notifications for user {user_id}: {e}")
            raise
            
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            await self.repository.mark_as_read(notification_id)
            logger.info(f"Marked notification {notification_id} as read")
            return True
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            raise
            
    async def create_maintenance_due_notification(self, 
                                                 maintenance_record: Dict[str, Any],
                                                 recipient_roles: List[str] = None) -> Dict[str, Any]:
        """Create notification for upcoming maintenance"""
        try:
            if recipient_roles is None:
                recipient_roles = ["fleet_manager", "maintenance_supervisor"]
                
            vehicle_id = maintenance_record.get("vehicle_id", "Unknown")
            scheduled_date = maintenance_record.get("scheduled_date")
            
            if isinstance(scheduled_date, str):
                scheduled_date = datetime.fromisoformat(scheduled_date.replace("Z", "+00:00"))
                
            notification_data = {
                "title": f"Maintenance Due - Vehicle {vehicle_id}",
                "message": f"Maintenance '{maintenance_record.get('title', 'Unknown')}' is scheduled for {scheduled_date.strftime('%Y-%m-%d %H:%M')}",
                "notification_type": "maintenance_due",
                "priority": maintenance_record.get("priority", MaintenancePriority.MEDIUM),
                "vehicle_id": vehicle_id,
                "maintenance_record_id": maintenance_record.get("id"),
                "recipient_roles": recipient_roles
            }
            
            return await self.create_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error creating maintenance due notification: {e}")
            raise
            
    async def create_license_expiry_notification(self,
                                               license_record: Dict[str, Any],
                                               recipient_roles: List[str] = None) -> Dict[str, Any]:
        """Create notification for expiring license"""
        try:
            if recipient_roles is None:
                recipient_roles = ["fleet_manager", "compliance_officer"]
                
            entity_id = license_record.get("entity_id", "Unknown")
            entity_type = license_record.get("entity_type", "Unknown")
            license_type = license_record.get("license_type", "Unknown")
            expiry_date = license_record.get("expiry_date")
            
            if isinstance(expiry_date, str):
                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                
            days_until_expiry = (expiry_date - date.today()).days
            
            notification_data = {
                "title": f"License Expiring - {entity_type.title()} {entity_id}",
                "message": f"{license_type.replace('_', ' ').title()} expires in {days_until_expiry} days ({expiry_date})",
                "notification_type": "license_expiry",
                "priority": MaintenancePriority.HIGH if days_until_expiry <= 7 else MaintenancePriority.MEDIUM,
                "vehicle_id": entity_id if entity_type == "vehicle" else None,
                "license_record_id": license_record.get("id"),
                "recipient_roles": recipient_roles
            }
            
            return await self.create_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error creating license expiry notification: {e}")
            raise
            
    async def create_overdue_maintenance_notification(self,
                                                    maintenance_record: Dict[str, Any],
                                                    recipient_roles: List[str] = None) -> Dict[str, Any]:
        """Create notification for overdue maintenance"""
        try:
            if recipient_roles is None:
                recipient_roles = ["fleet_manager", "maintenance_supervisor"]
                
            vehicle_id = maintenance_record.get("vehicle_id", "Unknown")
            scheduled_date = maintenance_record.get("scheduled_date")
            
            if isinstance(scheduled_date, str):
                scheduled_date = datetime.fromisoformat(scheduled_date.replace("Z", "+00:00"))
                
            days_overdue = (datetime.utcnow() - scheduled_date).days
            
            notification_data = {
                "title": f"OVERDUE Maintenance - Vehicle {vehicle_id}",
                "message": f"Maintenance '{maintenance_record.get('title', 'Unknown')}' is {days_overdue} days overdue (was due {scheduled_date.strftime('%Y-%m-%d')})",
                "notification_type": "maintenance_overdue",
                "priority": MaintenancePriority.CRITICAL,
                "vehicle_id": vehicle_id,
                "maintenance_record_id": maintenance_record.get("id"),
                "recipient_roles": recipient_roles
            }
            
            return await self.create_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error creating overdue maintenance notification: {e}")
            raise
            
    async def create_maintenance_completed_notification(self,
                                                      maintenance_record: Dict[str, Any],
                                                      recipient_roles: List[str] = None) -> Dict[str, Any]:
        """Create notification for completed maintenance"""
        try:
            if recipient_roles is None:
                recipient_roles = ["fleet_manager"]
                
            vehicle_id = maintenance_record.get("vehicle_id", "Unknown")
            actual_cost = maintenance_record.get("actual_cost", 0)
            
            notification_data = {
                "title": f"Maintenance Completed - Vehicle {vehicle_id}",
                "message": f"Maintenance '{maintenance_record.get('title', 'Unknown')}' completed. Cost: ${actual_cost:.2f}",
                "notification_type": "maintenance_completed",
                "priority": MaintenancePriority.LOW,
                "vehicle_id": vehicle_id,
                "maintenance_record_id": maintenance_record.get("id"),
                "recipient_roles": recipient_roles
            }
            
            return await self.create_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error creating maintenance completed notification: {e}")
            raise
            
    async def process_pending_notifications(self) -> int:
        """Process and send pending notifications"""
        try:
            pending_notifications = await self.get_pending_notifications()
            sent_count = 0
            
            for notification in pending_notifications:
                try:
                    # Here you would integrate with actual notification delivery service
                    # For now, just mark as sent
                    await self.send_notification(notification["id"])
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to send notification {notification['id']}: {e}")
                    
            logger.info(f"Processed {sent_count} notifications")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error processing pending notifications: {e}")
            raise


# Global service instance
notification_service = NotificationService()
