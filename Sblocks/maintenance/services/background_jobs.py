"""
Background jobs for Maintenance Service
Handles automated status updates, notifications, and periodic tasks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from services.maintenance_service import maintenance_records_service
from services.notification_service import notification_service
from services.license_service import license_service

logger = logging.getLogger(__name__)


class MaintenanceBackgroundJobs:
    """Background job manager for maintenance service"""
    
    def __init__(self):
        self.is_running = False
        self.tasks = []
        
    async def start_background_jobs(self):
        """Start all background jobs"""
        if self.is_running:
            logger.warning("Background jobs already running")
            return
            
        self.is_running = True
        logger.info("Starting maintenance background jobs...")
        
        # Create background tasks
        self.tasks = [
            asyncio.create_task(self._overdue_status_updater()),
            asyncio.create_task(self._notification_sender()),
            asyncio.create_task(self._license_expiry_checker()),
            asyncio.create_task(self._maintenance_reminder_generator()),
        ]
        
        logger.info(f"Started {len(self.tasks)} background jobs")
        
    async def stop_background_jobs(self):
        """Stop all background jobs"""
        if not self.is_running:
            return
            
        logger.info("Stopping maintenance background jobs...")
        self.is_running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
            
        # Wait for tasks to complete cancellation
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        
        logger.info("Background jobs stopped")
        
    async def _overdue_status_updater(self):
        """Update overdue maintenance records every hour"""
        while self.is_running:
            try:
                logger.info("Running overdue status update job...")
                
                updated_records = await maintenance_records_service.update_overdue_statuses()
                
                if updated_records:
                    logger.info(f"Updated {len(updated_records)} records to overdue status")
                    
                    # Generate notifications for newly overdue items
                    for record in updated_records:
                        await self._generate_overdue_notification(record)
                else:
                    logger.debug("No overdue maintenance records found")
                    
            except Exception as e:
                logger.error(f"Error in overdue status updater: {e}", exc_info=True)
                
            # Wait 1 hour before next run
            await asyncio.sleep(3600)
            
    async def _notification_sender(self):
        """Send scheduled notifications every 15 minutes"""
        while self.is_running:
            try:
                logger.debug("Checking for scheduled notifications...")
                
                # Get notifications that should be sent now
                notifications = await notification_service.get_pending_notifications()
                
                for notification in notifications:
                    try:
                        await notification_service.send_notification(notification)
                        logger.info(f"Sent notification {notification['id']}")
                    except Exception as e:
                        logger.error(f"Failed to send notification {notification['id']}: {e}")
                        
            except Exception as e:
                logger.error(f"Error in notification sender: {e}", exc_info=True)
                
            # Wait 15 minutes before next run
            await asyncio.sleep(900)
            
    async def _license_expiry_checker(self):
        """Check for expiring licenses daily"""
        while self.is_running:
            try:
                logger.info("Checking for expiring licenses...")
                
                # Check for licenses expiring in the next 30 days
                expiring_licenses = await license_service.get_expiring_licenses(days_ahead=30)
                
                for license_record in expiring_licenses:
                    await self._generate_license_expiry_notification(license_record)
                    
                logger.info(f"Processed {len(expiring_licenses)} expiring licenses")
                
            except Exception as e:
                logger.error(f"Error in license expiry checker: {e}", exc_info=True)
                
            # Wait 24 hours before next run
            await asyncio.sleep(86400)
            
    async def _maintenance_reminder_generator(self):
        """Generate maintenance reminders based on schedules and mileage"""
        while self.is_running:
            try:
                logger.info("Generating maintenance reminders...")
                
                # This would integrate with vehicle service to get current mileage
                # and generate maintenance reminders based on schedules
                
                # For now, just check upcoming maintenance (next 7 days)
                upcoming_maintenance = await maintenance_records_service.get_upcoming_maintenance(7)
                
                for record in upcoming_maintenance:
                    # Check if reminder already exists
                    existing_notifications = await notification_service.get_notifications_for_maintenance(
                        record['id']
                    )
                    
                    if not existing_notifications:
                        await self._generate_reminder_notification(record)
                        
                logger.info(f"Processed {len(upcoming_maintenance)} upcoming maintenance items")
                
            except Exception as e:
                logger.error(f"Error in maintenance reminder generator: {e}", exc_info=True)
                
            # Wait 6 hours before next run
            await asyncio.sleep(21600)
            
    async def _generate_overdue_notification(self, record: Dict[str, Any]):
        """Generate notification for overdue maintenance"""
        try:
            notification_data = {
                "vehicle_id": record["vehicle_id"],
                "maintenance_record_id": record["id"],
                "type": "overdue_maintenance",
                "priority": "high",
                "title": "Overdue Maintenance",
                "message": f"Maintenance '{record['title']}' is overdue (scheduled: {record['scheduled_date']})",
                "scheduled_send_time": datetime.utcnow(),
                "recipient_user_ids": [],  # Would be populated based on vehicle assignment
                "metadata": {
                    "maintenance_type": record.get("maintenance_type"),
                    "priority": record.get("priority"),
                    "overdue_days": (datetime.utcnow() - record["scheduled_date"]).days
                }
            }
            
            await notification_service.create_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error generating overdue notification: {e}")
            
    async def _generate_license_expiry_notification(self, license_record: Dict[str, Any]):
        """Generate notification for expiring license"""
        try:
            days_until_expiry = (license_record["expiry_date"] - datetime.utcnow()).days
            
            notification_data = {
                "entity_id": license_record["entity_id"],
                "license_record_id": license_record["id"],
                "type": "license_expiry",
                "priority": "high" if days_until_expiry <= 7 else "medium",
                "title": "License Expiring Soon",
                "message": f"License '{license_record['license_type']}' expires in {days_until_expiry} days",
                "scheduled_send_time": datetime.utcnow(),
                "recipient_user_ids": [],  # Would be populated based on entity ownership
                "metadata": {
                    "license_type": license_record["license_type"],
                    "expiry_date": license_record["expiry_date"].isoformat(),
                    "days_until_expiry": days_until_expiry
                }
            }
            
            await notification_service.create_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error generating license expiry notification: {e}")
            
    async def _generate_reminder_notification(self, record: Dict[str, Any]):
        """Generate reminder notification for upcoming maintenance"""
        try:
            days_until_due = (record["scheduled_date"] - datetime.utcnow()).days
            
            notification_data = {
                "vehicle_id": record["vehicle_id"],
                "maintenance_record_id": record["id"],
                "type": "maintenance_reminder",
                "priority": "medium",
                "title": "Upcoming Maintenance",
                "message": f"Maintenance '{record['title']}' is due in {days_until_due} days",
                "scheduled_send_time": datetime.utcnow(),
                "recipient_user_ids": [],  # Would be populated based on vehicle assignment
                "metadata": {
                    "maintenance_type": record.get("maintenance_type"),
                    "scheduled_date": record["scheduled_date"].isoformat(),
                    "days_until_due": days_until_due
                }
            }
            
            await notification_service.create_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error generating reminder notification: {e}")


# Global instance
background_jobs = MaintenanceBackgroundJobs()
