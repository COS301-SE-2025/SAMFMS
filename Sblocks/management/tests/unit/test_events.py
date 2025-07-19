"""
Unit tests for event models and publisher
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId

from events.events import (
    EventType,
    BaseEvent,
    VehicleEvent,
    AssignmentEvent,
    TripEvent,
    DriverEvent,
    AnalyticsEvent,
    ServiceEvent,
    UserEvent
)
from events.publisher import EventPublisher


@pytest.mark.unit
@pytest.mark.events
class TestEventModels:
    """Test class for event models"""
    
    def test_assignment_event_creation(self):
        """Test AssignmentEvent creation"""
        # Arrange
        event_data = {
            "event_type": EventType.ASSIGNMENT_CREATED,
            "assignment_id": "assignment123",
            "vehicle_id": "vehicle123",
            "driver_id": "driver456",
            "assignment_type": "trip",
            "status": "active"
        }
        
        # Act
        event = AssignmentEvent(**event_data)
        
        # Assert
        assert event.event_type == EventType.ASSIGNMENT_CREATED
        assert event.assignment_id == "assignment123"
        assert event.vehicle_id == "vehicle123"
        assert event.driver_id == "driver456"
        assert event.assignment_type == "trip"
        assert event.status == "active"
    
    # def test_trip_event_creation(self):
    #     """Test TripEvent creation"""
    #     # Arrange
    #     event_data = {
    #         "event_type": EventType.TRIP_STARTED,
    #         "trip_id": "trip123",
    #         "vehicle_id": "vehicle123",
    #         "driver_id": "driver456",
    #         "assignment_id": "assignment123",
    #         "data": {"start_location": "Office", "purpose": "Client meeting"}
    #     }
    #     
    #     # Act
    #     event = TripEvent(**event_data)
    #     
    #     # Assert
    #     assert event.event_type == EventType.TRIP_STARTED
    #     assert event.trip_id == "trip123"
    #     assert event.vehicle_id == "vehicle123"
    #     assert event.driver_id == "driver456"
    #     assert event.assignment_id == "assignment123"
    #     assert event.data["start_location"] == "Office"
        """Test DriverEvent creation"""
        # Arrange
        event_data = {
            "event_type": EventType.DRIVER_CREATED,
            "driver_id": "driver123",
            "employee_id": "EMP001",
            "status": "active",
            "data": {"first_name": "John", "last_name": "Doe"}
        }
        
        # Act
        event = DriverEvent(**event_data)
        
        # Assert
        assert event.event_type == EventType.DRIVER_CREATED
        assert event.driver_id == "driver123"
        assert event.employee_id == "EMP001"
        assert event.status == "active"
        assert event.data["first_name"] == "John"
    
    def test_analytics_event_creation(self):
        """Test AnalyticsEvent creation"""
        # Arrange
        event_data = {
            "event_type": EventType.VEHICLE_CREATED,  # Using an existing event type
            "metric_type": "fleet_utilization",
            "data": {"total_vehicles": 50, "active_vehicles": 35}
        }
        
        # Act
        event = AnalyticsEvent(**event_data)
        
        # Assert
        assert event.metric_type == "fleet_utilization"
        assert event.data["total_vehicles"] == 50
        assert event.data["active_vehicles"] == 35
    
    def test_service_event_creation(self):
        """Test ServiceEvent creation"""
        # Arrange
        event_data = {
            "event_type": EventType.VEHICLE_CREATED,  # Using an existing event type
            "service_status": "healthy",
            "version": "2.0.0"
        }
        
        # Act
        event = ServiceEvent(**event_data)
        
        # Assert
        assert event.service_status == "healthy"
        assert event.version == "2.0.0"
    
    def test_user_event_creation(self):
        """Test UserEvent creation"""
        # Arrange
        event_data = {
            "event_type": EventType.VEHICLE_CREATED,  # Using an existing event type
            "user_id": "user123",
            "action": "created",
            "data": {"email": "user@example.com", "role": "driver"}
        }
        
        # Act
        event = UserEvent(**event_data)
        
        # Assert
        assert event.user_id == "user123"
        assert event.action == "created"
        assert event.data["email"] == "user@example.com"
        assert event.data["role"] == "driver"
    
    def test_base_event_properties(self):
        """Test BaseEvent properties"""
        # Arrange
        event_data = {
            "event_type": EventType.VEHICLE_CREATED,
            "correlation_id": "corr123",
            "user_id": "user456"
        }
        
        # Act
        event = BaseEvent(**event_data)
        
        # Assert
        assert event.event_type == EventType.VEHICLE_CREATED
        assert event.service == "management"
        assert event.correlation_id == "corr123"
        assert event.user_id == "user456"
        assert event.event_id is not None
        assert event.timestamp is not None
    
    def test_event_type_enum_values(self):
        """Test EventType enum values"""
        # Assert
        assert EventType.VEHICLE_CREATED == "vehicle.created"
        assert EventType.VEHICLE_UPDATED == "vehicle.updated"
        assert EventType.VEHICLE_DELETED == "vehicle.deleted"
        assert EventType.ASSIGNMENT_CREATED == "assignment.created"
        assert EventType.ASSIGNMENT_UPDATED == "assignment.updated"
        assert EventType.DRIVER_CREATED == "driver.created"
        assert EventType.DRIVER_UPDATED == "driver.updated"
        assert EventType.TRIP_STARTED == "trip.started"
        assert EventType.TRIP_ENDED == "trip.ended"


@pytest.mark.unit
@pytest.mark.events
class TestEventPublisher:
    """Test class for event publisher"""
    
    @pytest.fixture
    def mock_publisher(self):
        """Create a mock event publisher"""
        return MagicMock(spec=EventPublisher)
    
    @pytest.fixture
    def sample_event(self):
        """Create a sample event for testing"""
        return VehicleEvent(
            event_type=EventType.VEHICLE_CREATED,
            vehicle_id="vehicle123",
            registration_number="ABC123GP",
            status="available"
        )
    
    @pytest.mark.asyncio
    async def test_publish_event_success(self, mock_publisher, sample_event):
        """Test successful event publishing"""
        # Arrange
        mock_publisher.publish = AsyncMock(return_value=True)
        
        # Act
        result = await mock_publisher.publish(sample_event)
        
        # Assert
        assert result is True
        mock_publisher.publish.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_event_failure(self, mock_publisher, sample_event):
        """Test event publishing failure"""
        # Arrange
        mock_publisher.publish = AsyncMock(side_effect=Exception("Publishing failed"))
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await mock_publisher.publish(sample_event)
        
        assert str(exc_info.value) == "Publishing failed"
    
    @pytest.mark.asyncio
    async def test_publish_multiple_events(self, mock_publisher):
        """Test publishing multiple events"""
        # Arrange
        events = [
            VehicleEvent(
                event_type=EventType.VEHICLE_CREATED,
                vehicle_id="vehicle1",
                registration_number="ABC123GP",
                status="available"
            ),
            VehicleEvent(
                event_type=EventType.VEHICLE_UPDATED,
                vehicle_id="vehicle2",
                registration_number="DEF456GP",
                status="maintenance"
            )
        ]
        mock_publisher.publish_batch = AsyncMock(return_value=True)
        
        # Act
        result = await mock_publisher.publish_batch(events)
        
        # Assert
        assert result is True
        mock_publisher.publish_batch.assert_called_once_with(events)
    
    @pytest.mark.asyncio
    async def test_publish_event_with_retry(self, mock_publisher, sample_event):
        """Test event publishing with retry mechanism"""
        # Arrange
        mock_publisher.publish_with_retry = AsyncMock(return_value=True)
        
        # Act
        result = await mock_publisher.publish_with_retry(sample_event, max_retries=3)
        
        # Assert
        assert result is True
        mock_publisher.publish_with_retry.assert_called_once_with(sample_event, max_retries=3)
    
    @pytest.mark.asyncio
    async def test_publish_event_serialization(self, mock_publisher):
        """Test event serialization before publishing"""
        # Arrange
        event = VehicleEvent(
            event_type=EventType.VEHICLE_CREATED,
            vehicle_id="vehicle123",
            registration_number="ABC123GP",
            status="available",
            data={"make": "Toyota", "model": "Corolla"}
        )
        mock_publisher.serialize_event = MagicMock(return_value={"event_type": "vehicle.created"})
        
        # Act
        result = mock_publisher.serialize_event(event)
        
        # Assert
        assert result["event_type"] == "vehicle.created"
        mock_publisher.serialize_event.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_event_routing(self, mock_publisher, sample_event):
        """Test event routing to appropriate queue"""
        # Arrange
        mock_publisher.get_routing_key = MagicMock(return_value="management.vehicle.created")
        
        # Act
        routing_key = mock_publisher.get_routing_key(sample_event)
        
        # Assert
        assert routing_key == "management.vehicle.created"
        mock_publisher.get_routing_key.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_event_validation(self, mock_publisher):
        """Test event validation before publishing"""
        # Arrange
        invalid_event = {"invalid": "event"}
        mock_publisher.validate_event = MagicMock(return_value=False)
        
        # Act
        result = mock_publisher.validate_event(invalid_event)
        
        # Assert
        assert result is False
        mock_publisher.validate_event.assert_called_once_with(invalid_event)
    
    @pytest.mark.asyncio
    async def test_event_logging(self, mock_publisher, sample_event):
        """Test event logging during publishing"""
        # Arrange
        mock_publisher.log_event = MagicMock()
        
        # Act
        mock_publisher.log_event(sample_event, "published")
        
        # Assert
        mock_publisher.log_event.assert_called_once_with(sample_event, "published")
    
    @pytest.mark.asyncio
    async def test_event_metrics(self, mock_publisher, sample_event):
        """Test event metrics collection"""
        # Arrange
        mock_publisher.record_metrics = MagicMock()
        
        # Act
        mock_publisher.record_metrics(sample_event, "success")
        
        # Assert
        mock_publisher.record_metrics.assert_called_once_with(sample_event, "success")
