"""
Unit tests for event consumer
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone
import json
from bson import ObjectId

from events.consumer import (
    VehicleEventConsumer, 
    AssignmentEventConsumer, 
    AnalyticsEventConsumer,
    EventConsumerManager,
    EventConsumerError
)
from events.events import (
    VehicleCreatedEvent,
    VehicleUpdatedEvent,
    AssignmentCreatedEvent,
    AssignmentUpdatedEvent,
    AnalyticsEvent
)


@pytest.mark.unit
@pytest.mark.consumer
class TestVehicleEventConsumer:
    """Test class for VehicleEventConsumer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.consumer = VehicleEventConsumer()
        self.mock_channel = AsyncMock()
        self.mock_message = MagicMock()
        
        # Mock event data
        self.vehicle_id = str(ObjectId())
        self.vehicle_data = {
            "vehicle_id": self.vehicle_id,
            "registration_number": "ABC-001",
            "make": "Toyota",
            "model": "Camry",
            "status": "available",
            "department": "operations",
            "user_id": "test_user",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_consume_vehicle_created_event_success(self):
        """Test consuming vehicle created event successfully"""
        # Arrange
        event_data = {
            "event_type": "vehicle.created",
            "data": self.vehicle_data
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.vehicle_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_vehicle_created = AsyncMock()
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_service.process_vehicle_created.assert_called_once()
            mock_logger.info.assert_called()
            self.mock_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_vehicle_updated_event_success(self):
        """Test consuming vehicle updated event successfully"""
        # Arrange
        event_data = {
            "event_type": "vehicle.updated",
            "data": {
                **self.vehicle_data,
                "previous_status": "in_use",
                "new_status": "available"
            }
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.vehicle_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_vehicle_updated = AsyncMock()
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_service.process_vehicle_updated.assert_called_once()
            mock_logger.info.assert_called()
            self.mock_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_vehicle_deleted_event_success(self):
        """Test consuming vehicle deleted event successfully"""
        # Arrange
        event_data = {
            "event_type": "vehicle.deleted",
            "data": {
                "vehicle_id": self.vehicle_id,
                "registration_number": "ABC-001",
                "user_id": "test_user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.vehicle_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_vehicle_deleted = AsyncMock()
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_service.process_vehicle_deleted.assert_called_once()
            mock_logger.info.assert_called()
            self.mock_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_invalid_json_error(self):
        """Test error handling for invalid JSON"""
        # Arrange
        self.mock_message.body = b"invalid json"
        
        with patch('events.consumer.logger') as mock_logger:
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_logger.error.assert_called()
            self.mock_message.nack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_unknown_event_type(self):
        """Test handling of unknown event types"""
        # Arrange
        event_data = {
            "event_type": "unknown.event",
            "data": self.vehicle_data
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.logger') as mock_logger:
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_logger.warning.assert_called()
            self.mock_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_service_error_handling(self):
        """Test error handling when service raises exception"""
        # Arrange
        event_data = {
            "event_type": "vehicle.created",
            "data": self.vehicle_data
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.vehicle_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_vehicle_created = AsyncMock(
                side_effect=Exception("Service error")
            )
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_logger.error.assert_called()
            self.mock_message.nack.assert_called_once()


@pytest.mark.unit
@pytest.mark.consumer
class TestAssignmentEventConsumer:
    """Test class for AssignmentEventConsumer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.consumer = AssignmentEventConsumer()
        self.mock_channel = AsyncMock()
        self.mock_message = MagicMock()
        
        # Mock event data
        self.assignment_id = str(ObjectId())
        self.assignment_data = {
            "assignment_id": self.assignment_id,
            "vehicle_id": str(ObjectId()),
            "driver_id": str(ObjectId()),
            "assignment_type": "regular",
            "status": "active",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "user_id": "test_user",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_consume_assignment_created_event_success(self):
        """Test consuming assignment created event successfully"""
        # Arrange
        event_data = {
            "event_type": "assignment.created",
            "data": self.assignment_data
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.assignment_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_assignment_created = AsyncMock()
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_service.process_assignment_created.assert_called_once()
            mock_logger.info.assert_called()
            self.mock_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_assignment_updated_event_success(self):
        """Test consuming assignment updated event successfully"""
        # Arrange
        event_data = {
            "event_type": "assignment.updated",
            "data": {
                **self.assignment_data,
                "previous_status": "active",
                "new_status": "completed"
            }
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.assignment_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_assignment_updated = AsyncMock()
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_service.process_assignment_updated.assert_called_once()
            mock_logger.info.assert_called()
            self.mock_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_assignment_completed_event_success(self):
        """Test consuming assignment completed event successfully"""
        # Arrange
        event_data = {
            "event_type": "assignment.completed",
            "data": {
                **self.assignment_data,
                "status": "completed",
                "completion_date": datetime.now(timezone.utc).isoformat(),
                "total_distance": 150.5,
                "fuel_consumed": 12.3
            }
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.assignment_service') as mock_service, \
             patch('events.consumer.analytics_service') as mock_analytics, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_assignment_completed = AsyncMock()
            mock_analytics.update_assignment_metrics = AsyncMock()
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_service.process_assignment_completed.assert_called_once()
            mock_analytics.update_assignment_metrics.assert_called_once()
            mock_logger.info.assert_called()
            self.mock_message.ack.assert_called_once()


@pytest.mark.unit
@pytest.mark.consumer
class TestAnalyticsEventConsumer:
    """Test class for AnalyticsEventConsumer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.consumer = AnalyticsEventConsumer()
        self.mock_channel = AsyncMock()
        self.mock_message = MagicMock()
        
        # Mock event data
        self.analytics_data = {
            "metric_type": "fleet_utilization",
            "metric_value": 85.5,
            "period": "daily",
            "department": "operations",
            "user_id": "test_user",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_consume_analytics_update_event_success(self):
        """Test consuming analytics update event successfully"""
        # Arrange
        event_data = {
            "event_type": "analytics.updated",
            "data": self.analytics_data
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.analytics_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_analytics_update = AsyncMock()
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_service.process_analytics_update.assert_called_once()
            mock_logger.info.assert_called()
            self.mock_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_analytics_snapshot_event_success(self):
        """Test consuming analytics snapshot event successfully"""
        # Arrange
        event_data = {
            "event_type": "analytics.snapshot",
            "data": {
                **self.analytics_data,
                "snapshot_data": {
                    "total_vehicles": 25,
                    "active_assignments": 15,
                    "fuel_efficiency": 12.5
                }
            }
        }
        
        message_body = json.dumps(event_data)
        self.mock_message.body = message_body.encode('utf-8')
        
        with patch('events.consumer.analytics_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_analytics_snapshot = AsyncMock()
            
            # Act
            await self.consumer.consume_message(self.mock_channel, self.mock_message)
            
            # Assert
            mock_service.process_analytics_snapshot.assert_called_once()
            mock_logger.info.assert_called()
            self.mock_message.ack.assert_called_once()


@pytest.mark.unit
@pytest.mark.consumer
class TestEventConsumerManager:
    """Test class for EventConsumerManager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = EventConsumerManager()
        
    @pytest.mark.asyncio
    async def test_start_consumers_success(self):
        """Test starting consumers successfully"""
        # Arrange
        with patch('events.consumer.connect_robust') as mock_connect, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_connection = AsyncMock()
            mock_channel = AsyncMock()
            mock_queue = AsyncMock()
            
            mock_connect.return_value = mock_connection
            mock_connection.channel.return_value = mock_channel
            mock_channel.declare_queue.return_value = mock_queue
            
            # Act
            await self.manager.start_consumers()
            
            # Assert
            mock_connect.assert_called_once()
            mock_connection.channel.assert_called()
            mock_channel.declare_queue.assert_called()
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_start_consumers_connection_error(self):
        """Test error handling when connection fails"""
        # Arrange
        with patch('events.consumer.connect_robust') as mock_connect, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_connect.side_effect = Exception("Connection failed")
            
            # Act
            await self.manager.start_consumers()
            
            # Assert
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_stop_consumers_success(self):
        """Test stopping consumers successfully"""
        # Arrange
        mock_connection = AsyncMock()
        self.manager.connection = mock_connection
        
        with patch('events.consumer.logger') as mock_logger:
            
            # Act
            await self.manager.stop_consumers()
            
            # Assert
            mock_connection.close.assert_called_once()
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_stop_consumers_no_connection(self):
        """Test stopping consumers when no connection exists"""
        # Arrange
        self.manager.connection = None
        
        with patch('events.consumer.logger') as mock_logger:
            
            # Act
            await self.manager.stop_consumers()
            
            # Assert
            mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_register_consumer_success(self):
        """Test registering a consumer successfully"""
        # Arrange
        mock_consumer = MagicMock()
        queue_name = "test_queue"
        
        # Act
        self.manager.register_consumer(queue_name, mock_consumer)
        
        # Assert
        assert queue_name in self.manager.consumers
        assert self.manager.consumers[queue_name] == mock_consumer
    
    @pytest.mark.asyncio
    async def test_unregister_consumer_success(self):
        """Test unregistering a consumer successfully"""
        # Arrange
        mock_consumer = MagicMock()
        queue_name = "test_queue"
        self.manager.register_consumer(queue_name, mock_consumer)
        
        # Act
        self.manager.unregister_consumer(queue_name)
        
        # Assert
        assert queue_name not in self.manager.consumers
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check when consumers are healthy"""
        # Arrange
        mock_connection = AsyncMock()
        mock_connection.is_closed = False
        self.manager.connection = mock_connection
        
        # Act
        health_status = await self.manager.health_check()
        
        # Assert
        assert health_status["status"] == "healthy"
        assert health_status["connection_open"] is True
        assert "consumers_registered" in health_status
    
    @pytest.mark.asyncio
    async def test_health_check_connection_closed(self):
        """Test health check when connection is closed"""
        # Arrange
        mock_connection = AsyncMock()
        mock_connection.is_closed = True
        self.manager.connection = mock_connection
        
        # Act
        health_status = await self.manager.health_check()
        
        # Assert
        assert health_status["status"] == "unhealthy"
        assert health_status["connection_open"] is False
    
    @pytest.mark.asyncio
    async def test_health_check_no_connection(self):
        """Test health check when no connection exists"""
        # Arrange
        self.manager.connection = None
        
        # Act
        health_status = await self.manager.health_check()
        
        # Assert
        assert health_status["status"] == "unhealthy"
        assert health_status["connection_open"] is False


@pytest.mark.unit
@pytest.mark.consumer
class TestEventConsumerIntegration:
    """Test class for event consumer integration scenarios"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = EventConsumerManager()
        self.vehicle_consumer = VehicleEventConsumer()
        self.assignment_consumer = AssignmentEventConsumer()
        self.analytics_consumer = AnalyticsEventConsumer()
    
    @pytest.mark.asyncio
    async def test_full_event_flow_success(self):
        """Test complete event flow from creation to analytics"""
        # Arrange
        vehicle_id = str(ObjectId())
        driver_id = str(ObjectId())
        assignment_id = str(ObjectId())
        
        # Mock message setup
        mock_channel = AsyncMock()
        
        # Vehicle created event
        vehicle_created_msg = MagicMock()
        vehicle_created_data = {
            "event_type": "vehicle.created",
            "data": {
                "vehicle_id": vehicle_id,
                "registration_number": "ABC-001",
                "make": "Toyota",
                "model": "Camry",
                "status": "available",
                "user_id": "test_user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        vehicle_created_msg.body = json.dumps(vehicle_created_data).encode('utf-8')
        
        # Assignment created event
        assignment_created_msg = MagicMock()
        assignment_created_data = {
            "event_type": "assignment.created",
            "data": {
                "assignment_id": assignment_id,
                "vehicle_id": vehicle_id,
                "driver_id": driver_id,
                "assignment_type": "regular",
                "status": "active",
                "user_id": "test_user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        assignment_created_msg.body = json.dumps(assignment_created_data).encode('utf-8')
        
        with patch('events.consumer.vehicle_service') as mock_vehicle_service, \
             patch('events.consumer.assignment_service') as mock_assignment_service, \
             patch('events.consumer.analytics_service') as mock_analytics_service:
            
            mock_vehicle_service.process_vehicle_created = AsyncMock()
            mock_assignment_service.process_assignment_created = AsyncMock()
            mock_analytics_service.update_fleet_metrics = AsyncMock()
            
            # Act
            await self.vehicle_consumer.consume_message(mock_channel, vehicle_created_msg)
            await self.assignment_consumer.consume_message(mock_channel, assignment_created_msg)
            
            # Assert
            mock_vehicle_service.process_vehicle_created.assert_called_once()
            mock_assignment_service.process_assignment_created.assert_called_once()
            vehicle_created_msg.ack.assert_called_once()
            assignment_created_msg.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_retry_logic(self):
        """Test error recovery and retry logic"""
        # Arrange
        mock_channel = AsyncMock()
        mock_message = MagicMock()
        
        event_data = {
            "event_type": "vehicle.created",
            "data": {
                "vehicle_id": str(ObjectId()),
                "registration_number": "ABC-001",
                "user_id": "test_user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        mock_message.body = json.dumps(event_data).encode('utf-8')
        
        with patch('events.consumer.vehicle_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            # First call fails, second succeeds
            mock_service.process_vehicle_created = AsyncMock(
                side_effect=[Exception("Temporary error"), None]
            )
            
            # Act - First attempt (should fail)
            await self.vehicle_consumer.consume_message(mock_channel, mock_message)
            
            # Reset mock message
            mock_message.reset_mock()
            
            # Act - Second attempt (should succeed)  
            await self.vehicle_consumer.consume_message(mock_channel, mock_message)
            
            # Assert
            assert mock_service.process_vehicle_created.call_count == 2
            mock_logger.error.assert_called()
            mock_message.ack.assert_called_once()  # Only second attempt succeeds
    
    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self):
        """Test concurrent processing of multiple events"""
        # Arrange
        mock_channel = AsyncMock()
        
        # Create multiple messages
        messages = []
        for i in range(5):
            msg = MagicMock()
            event_data = {
                "event_type": "vehicle.created",
                "data": {
                    "vehicle_id": str(ObjectId()),
                    "registration_number": f"ABC-{i:03d}",
                    "user_id": "test_user",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            msg.body = json.dumps(event_data).encode('utf-8')
            messages.append(msg)
        
        with patch('events.consumer.vehicle_service') as mock_service:
            mock_service.process_vehicle_created = AsyncMock()
            
            # Act - Process all messages concurrently
            import asyncio
            await asyncio.gather(*[
                self.vehicle_consumer.consume_message(mock_channel, msg)
                for msg in messages
            ])
            
            # Assert
            assert mock_service.process_vehicle_created.call_count == 5
            for msg in messages:
                msg.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_event_consumer_error_custom_exception(self):
        """Test custom exception handling in event consumers"""
        # Arrange
        mock_channel = AsyncMock()
        mock_message = MagicMock()
        
        event_data = {
            "event_type": "vehicle.created",
            "data": {
                "vehicle_id": str(ObjectId()),
                "registration_number": "ABC-001",
                "user_id": "test_user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        mock_message.body = json.dumps(event_data).encode('utf-8')
        
        with patch('events.consumer.vehicle_service') as mock_service, \
             patch('events.consumer.logger') as mock_logger:
            
            mock_service.process_vehicle_created = AsyncMock(
                side_effect=EventConsumerError("Custom consumer error")
            )
            
            # Act
            await self.vehicle_consumer.consume_message(mock_channel, mock_message)
            
            # Assert
            mock_logger.error.assert_called()
            mock_message.nack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_event_consumer_metrics_tracking(self):
        """Test that event consumers track processing metrics"""
        # Arrange
        mock_channel = AsyncMock()
        mock_message = MagicMock()
        
        event_data = {
            "event_type": "vehicle.created",
            "data": {
                "vehicle_id": str(ObjectId()),
                "registration_number": "ABC-001",
                "user_id": "test_user",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        mock_message.body = json.dumps(event_data).encode('utf-8')
        
        with patch('events.consumer.vehicle_service') as mock_service, \
             patch('events.consumer.metrics_tracker') as mock_metrics:
            
            mock_service.process_vehicle_created = AsyncMock()
            mock_metrics.increment_counter = MagicMock()
            mock_metrics.record_duration = MagicMock()
            
            # Act
            await self.vehicle_consumer.consume_message(mock_channel, mock_message)
            
            # Assert
            mock_metrics.increment_counter.assert_called()
            mock_metrics.record_duration.assert_called()
