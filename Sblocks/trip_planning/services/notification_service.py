"""
Notification service for trip-related notifications
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager
from schemas.entities import Notification, NotificationPreferences, NotificationType, Trip
from schemas.requests import NotificationRequest, UpdateNotificationPreferencesRequest
from events.publisher import event_publisher

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing trip-related notifications"""
    
    def __init__(self):
        self.db = db_manager
        
    async def send_notification(self, request: NotificationRequest) -> List[Notification]:
        """Send notifications to specified users"""
        try:
            notifications = []
            
            for user_id in request.user_ids:
                # Get user notification preferences
                preferences = await self.get_user_preferences(user_id)
                
                # Check if user wants this type of notification
                if not self._should_send_notification(request.type, preferences):
                    logger.info(f"Skipping notification for user {user_id} due to preferences")
                    continue
                
                # Check quiet hours
                if preferences and self._is_quiet_hours(preferences):
                    logger.info(f"Skipping notification for user {user_id} due to quiet hours")
                    continue
                
                # Create notification
                notification_data = {
                    "user_id": user_id,
                    "type": request.type,
                    "title": request.title,
                    "message": request.message,
                    "trip_id": request.trip_id,
                    "driver_id": request.driver_id,
                    "data": request.data,
                    "channels": self._get_enabled_channels(request.channels, preferences),
                    "sent_at": request.scheduled_for or datetime.utcnow(),
                    "is_read": False
                }
                
                # Insert into database
                result = await self.db.notifications.insert_one(notification_data)
                
                # Create notification object
                notification_data["_id"] = str(result.inserted_id)
                notification = Notification(**notification_data)
                
                # Send through external channels
                await self._deliver_notification(notification, preferences)
                
                notifications.append(notification)
            
            logger.info(f"Sent {len(notifications)} notifications")
            return notifications
            
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
            raise
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        skip: int = 0
    ) -> tuple[List[Notification], int]:
        """Get notifications for a user"""
        try:
            query = {"user_id": user_id}
            
            if unread_only:
                query["is_read"] = False
            
            # Get total count
            total = await self.db.notifications.count_documents(query)
            
            # Get notifications
            cursor = self.db.notifications.find(query)
            cursor = cursor.sort("sent_at", -1).skip(skip).limit(limit)
            
            notifications = []
            async for notification_doc in cursor:
                notification_doc["_id"] = str(notification_doc["_id"])
                notifications.append(Notification(**notification_doc))
            
            return notifications, total
            
        except Exception as e:
            logger.error(f"Failed to get user notifications: {e}")
            raise
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            result = await self.db.notifications.update_one(
                {"_id": ObjectId(notification_id), "user_id": user_id},
                {
                    "$set": {
                        "is_read": True,
                        "read_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            raise
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            return await self.db.notifications.count_documents({
                "user_id": user_id,
                "is_read": False
            })
            
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0
    
    async def get_user_preferences(self, user_id: str) -> Optional[NotificationPreferences]:
        """Get notification preferences for a user"""
        try:
            preferences_doc = await self.db.notification_preferences.find_one({"user_id": user_id})
            
            if preferences_doc:
                preferences_doc["_id"] = str(preferences_doc["_id"])
                return NotificationPreferences(**preferences_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return None
    
    async def update_user_preferences(
        self,
        user_id: str,
        request: UpdateNotificationPreferencesRequest
    ) -> NotificationPreferences:
        """Update notification preferences for a user"""
        try:
            # Get existing preferences or create default
            existing = await self.get_user_preferences(user_id)
            
            if existing:
                # Update existing preferences
                update_data = request.dict(exclude_unset=True)
                update_data["updated_at"] = datetime.utcnow()
                
                await self.db.notification_preferences.update_one(
                    {"user_id": user_id},
                    {"$set": update_data}
                )
            else:
                # Create new preferences
                preferences_data = {
                    "user_id": user_id,
                    "updated_at": datetime.utcnow(),
                    **request.dict(exclude_unset=True)
                }
                
                await self.db.notification_preferences.insert_one(preferences_data)
            
            # Return updated preferences
            return await self.get_user_preferences(user_id)
            
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            raise
    
    # Trip-specific notification methods
    async def notify_trip_started(self, trip: Trip):
        """Send notification when a trip starts"""
        try:
            # Notify relevant users (trip creator, assigned driver, managers)
            user_ids = await self._get_trip_notification_recipients(trip)
            
            request = NotificationRequest(
                user_ids=user_ids,
                type=NotificationType.TRIP_STARTED,
                title="Trip Started",
                message=f"Trip '{trip.name}' has started",
                trip_id=trip.id,
                driver_id=trip.driver_assignment if trip.driver_assignment else None,
                channels=["push", "email"]
            )
            
            await self.send_notification(request)
            
        except Exception as e:
            logger.error(f"Failed to send trip started notification: {e}")
    
    async def notify_trip_completed(self, trip: Trip):
        """Send notification when a trip is completed"""
        try:
            user_ids = await self._get_trip_notification_recipients(trip)
            
            request = NotificationRequest(
                user_ids=user_ids,
                type=NotificationType.TRIP_COMPLETED,
                title="Trip Completed",
                message=f"Trip '{trip.name}' has been completed successfully",
                trip_id=trip.id,
                driver_id=trip.driver_assignment if trip.driver_assignment else None,
                channels=["push", "email"]
            )
            
            await self.send_notification(request)
            
        except Exception as e:
            logger.error(f"Failed to send trip completed notification: {e}")
    
    async def notify_trip_delayed(self, trip: Trip, delay_minutes: int):
        """Send notification when a trip is delayed"""
        try:
            user_ids = await self._get_trip_notification_recipients(trip)
            
            request = NotificationRequest(
                user_ids=user_ids,
                type=NotificationType.TRIP_DELAYED,
                title="Trip Delayed",
                message=f"Trip '{trip.name}' is delayed by {delay_minutes} minutes",
                trip_id=trip.id,
                driver_id=trip.driver_assignment if trip.driver_assignment else None,
                data={"delay_minutes": delay_minutes},
                channels=["push", "email", "sms"]
            )
            
            await self.send_notification(request)
            
        except Exception as e:
            logger.error(f"Failed to send trip delayed notification: {e}")
    
    async def notify_driver_assigned(self, trip: Trip, driver_id: str):
        """Send notification when a driver is assigned to a trip"""
        try:
            # Notify the driver and trip creator
            user_ids = [driver_id, trip.created_by]
            
            request = NotificationRequest(
                user_ids=user_ids,
                type=NotificationType.DRIVER_ASSIGNED,
                title="Driver Assigned",
                message=f"Driver has been assigned to trip '{trip.name}'",
                trip_id=trip.id,
                driver_id=driver_id,
                channels=["push", "email"]
            )
            
            await self.send_notification(request)
            
        except Exception as e:
            logger.error(f"Failed to send driver assigned notification: {e}")
    
    async def notify_route_changed(self, trip: Trip, reason: str):
        """Send notification when a trip route is changed"""
        try:
            user_ids = await self._get_trip_notification_recipients(trip)
            
            request = NotificationRequest(
                user_ids=user_ids,
                type=NotificationType.ROUTE_CHANGED,
                title="Route Changed",
                message=f"Route for trip '{trip.name}' has been updated. Reason: {reason}",
                trip_id=trip.id,
                driver_id=trip.driver_assignment if trip.driver_assignment else None,
                data={"reason": reason},
                channels=["push"]
            )
            
            await self.send_notification(request)
            
        except Exception as e:
            logger.error(f"Failed to send route changed notification: {e}")
    
    def _should_send_notification(
        self,
        notification_type: NotificationType,
        preferences: Optional[NotificationPreferences]
    ) -> bool:
        """Check if notification should be sent based on user preferences"""
        if not preferences:
            return True  # Default to sending if no preferences set
        
        type_mapping = {
            NotificationType.TRIP_STARTED: preferences.trip_started,
            NotificationType.TRIP_COMPLETED: preferences.trip_completed,
            NotificationType.TRIP_DELAYED: preferences.trip_delayed,
            NotificationType.DRIVER_LATE: preferences.driver_late,
            NotificationType.ROUTE_CHANGED: preferences.route_changed,
            NotificationType.TRAFFIC_ALERT: preferences.traffic_alert,
            NotificationType.DRIVER_ASSIGNED: preferences.driver_assigned,
            NotificationType.DRIVER_UNASSIGNED: preferences.driver_unassigned
        }
        
        return type_mapping.get(notification_type, True)
    
    def _is_quiet_hours(self, preferences: NotificationPreferences) -> bool:
        """Check if current time is within user's quiet hours"""
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False
        
        # Simplified quiet hours check - would need proper timezone handling
        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")
        
        return preferences.quiet_hours_start <= current_time <= preferences.quiet_hours_end
    
    def _get_enabled_channels(
        self,
        requested_channels: List[str],
        preferences: Optional[NotificationPreferences]
    ) -> List[str]:
        """Get enabled delivery channels for a user"""
        if not preferences:
            return requested_channels
        
        enabled_channels = []
        
        for channel in requested_channels:
            if channel == "email" and preferences.email_enabled:
                enabled_channels.append(channel)
            elif channel == "push" and preferences.push_enabled:
                enabled_channels.append(channel)
            elif channel == "sms" and preferences.sms_enabled:
                enabled_channels.append(channel)
        
        return enabled_channels or ["push"]  # Always fallback to push
    
    async def _deliver_notification(
        self,
        notification: Notification,
        preferences: Optional[NotificationPreferences]
    ):
        """Deliver notification through external channels"""
        try:
            delivery_status = {}
            
            for channel in notification.channels:
                if channel == "email":
                    success = await self._send_email(notification, preferences)
                    delivery_status["email"] = "sent" if success else "failed"
                elif channel == "push":
                    success = await self._send_push(notification)
                    delivery_status["push"] = "sent" if success else "failed"
                elif channel == "sms":
                    success = await self._send_sms(notification, preferences)
                    delivery_status["sms"] = "sent" if success else "failed"
            
            # Update delivery status in database
            await self.db.notifications.update_one(
                {"_id": ObjectId(notification.id)},
                {"$set": {"delivery_status": delivery_status}}
            )
            
        except Exception as e:
            logger.error(f"Failed to deliver notification {notification.id}: {e}")
    
    async def _send_email(
        self,
        notification: Notification,
        preferences: Optional[NotificationPreferences]
    ) -> bool:
        """Send email notification"""
        try:
            # This would integrate with email service
            # For now, just log
            email = preferences.email if preferences else None
            logger.info(f"Sending email notification to {email}: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def _send_push(self, notification: Notification) -> bool:
        """Send push notification"""
        try:
            # This would integrate with push notification service
            logger.info(f"Sending push notification to {notification.user_id}: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False
    
    async def _send_sms(
        self,
        notification: Notification,
        preferences: Optional[NotificationPreferences]
    ) -> bool:
        """Send SMS notification"""
        try:
            # This would integrate with SMS service
            phone = preferences.phone if preferences else None
            logger.info(f"Sending SMS notification to {phone}: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    async def _get_trip_notification_recipients(self, trip: Trip) -> List[str]:
        """Get list of users who should receive notifications for a trip"""
        recipients = [trip.created_by]
        
        if trip.driver_assignment:
            recipients.append(trip.driver_assignment)
        
        # Would also include managers, fleet operators, etc.
        
        return list(set(recipients))  # Remove duplicates


# Global instance
notification_service = NotificationService()
