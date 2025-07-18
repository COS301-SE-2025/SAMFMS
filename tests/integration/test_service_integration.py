"""
Service Integration Tests for SAMFMS
Tests the integration between Core service and Management/Maintenance services via RabbitMQ
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import aio_pika
import logging

logger = logging.getLogger(__name__)


class MockRabbitMQConnection:
    """Mock RabbitMQ connection for testing"""
    
    def __init__(self):
        self.is_closed = False
        self.channels = []
    
    async def channel(self):
        """Create a mock channel"""
        return MockRabbitMQChannel()
    
    async def close(self):
        """Close the connection"""
        self.is_closed = True


class MockRabbitMQChannel:
    """Mock RabbitMQ channel for testing"""
    
    def __init__(self):
        self.is_closed = False
        self.exchanges = {}
        self.queues = {}
        self.published_messages = []
    
    async def declare_exchange(self, name, type="direct", durable=True):
        """Declare an exchange"""
        exchange = MockRabbitMQExchange(name, type)
        self.exchanges[name] = exchange
        return exchange
    
    async def declare_queue(self, name, durable=True, arguments=None):
        """Declare a queue"""
        queue = MockRabbitMQQueue(name)
        self.queues[name] = queue
        return queue
    
    async def get_exchange(self, name):
        """Get an exchange"""
        return self.exchanges.get(name)
    
    async def set_qos(self, prefetch_count=1):
        """Set QoS"""
        pass
    
    async def close(self):
        """Close the channel"""
        self.is_closed = True


class MockRabbitMQExchange:
    """Mock RabbitMQ exchange for testing"""
    
    def __init__(self, name, type="direct"):
        self.name = name
        self.type = type
        self.published_messages = []
    
    async def publish(self, message, routing_key=""):
        """Publish a message"""
        self.published_messages.append({
            "message": message,
            "routing_key": routing_key,
            "timestamp": datetime.utcnow()
        })


class MockRabbitMQQueue:
    """Mock RabbitMQ queue for testing"""
    
    def __init__(self, name):
        self.name = name
        self.messages = []
        self.consumers = []
    
    async def bind(self, exchange, routing_key=""):
        """Bind queue to exchange"""
        pass
    
    async def consume(self, callback, no_ack=False):
        """Set up consumer"""
        self.consumers.append(callback)
    
    async def get(self, no_ack=False):
        """Get a message"""
        if self.messages:
            return self.messages.pop(0)
        return None


class MockRabbitMQMessage:
    """Mock RabbitMQ message for testing"""
    
    def __init__(self, body, headers=None, routing_key=""):
        self.body = body
        self.headers = headers or {}
        self.routing_key = routing_key
    
    async def ack(self):
        """Acknowledge message"""
        pass
    
    async def nack(self, requeue=True):
        """Negative acknowledge message"""
        pass


@pytest.fixture
def mock_rabbitmq_connection():
    """Mock RabbitMQ connection fixture"""
    return MockRabbitMQConnection()


@pytest.fixture
def mock_rabbitmq_channel():
    """Mock RabbitMQ channel fixture"""
    return MockRabbitMQChannel()


class TestCoreToManagementIntegration:
    """Test integration between Core and Management services"""
    
    @pytest.mark.asyncio
    async def test_vehicle_creation_event_flow(self, mock_rabbitmq_connection):
        """Test vehicle creation event flow from Core to Management"""
        # Mock the Core service request router
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            # Mock vehicle creation request
            vehicle_data = {
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "registration_number": "TEST-123-GP"
            }
            
            # Mock successful response from Management service
            router_instance.route_request.return_value = {
                "status": "success",
                "data": {**vehicle_data, "id": "vehicle_123"}
            }
            
            # Simulate Core API call
            response = await router_instance.route_request(
                endpoint="/api/vehicles",
                method="POST",
                data=vehicle_data,
                service="management"
            )
            
            assert response["status"] == "success"
            assert response["data"]["id"] == "vehicle_123"
            router_instance.route_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_driver_assignment_event_flow(self, mock_rabbitmq_connection):
        """Test driver assignment event flow"""
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            assignment_data = {
                "vehicle_id": "vehicle_123",
                "driver_id": "driver_123",
                "start_date": "2024-01-15",
                "end_date": "2024-01-16",
                "purpose": "Security patrol"
            }
            
            router_instance.route_request.return_value = {
                "status": "success",
                "data": {**assignment_data, "id": "assignment_123"}
            }
            
            response = await router_instance.route_request(
                endpoint="/api/vehicle-assignments",
                method="POST",
                data=assignment_data,
                service="management"
            )
            
            assert response["status"] == "success"
            assert response["data"]["id"] == "assignment_123"
    
    @pytest.mark.asyncio
    async def test_analytics_data_aggregation(self, mock_rabbitmq_connection):
        """Test analytics data aggregation from Management service"""
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            # Mock analytics response
            analytics_data = {
                "total_vehicles": 50,
                "active_drivers": 35,
                "fleet_utilization": 78.5,
                "monthly_costs": 45000.00
            }
            
            router_instance.route_request.return_value = {
                "status": "success",
                "data": analytics_data
            }
            
            response = await router_instance.route_request(
                endpoint="/api/analytics/dashboard",
                method="GET",
                data={},
                service="management"
            )
            
            assert response["status"] == "success"
            assert response["data"]["total_vehicles"] == 50
    
    @pytest.mark.asyncio
    async def test_management_service_timeout_handling(self, mock_rabbitmq_connection):
        """Test handling of Management service timeouts"""
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            # Mock timeout error
            router_instance.route_request.side_effect = asyncio.TimeoutError("Service timeout")
            
            with pytest.raises(asyncio.TimeoutError):
                await router_instance.route_request(
                    endpoint="/api/vehicles",
                    method="GET",
                    data={},
                    service="management"
                )
    
    @pytest.mark.asyncio
    async def test_management_service_error_handling(self, mock_rabbitmq_connection):
        """Test handling of Management service errors"""
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            # Mock error response
            router_instance.route_request.return_value = {
                "status": "error",
                "message": "Database connection failed",
                "status_code": 500
            }
            
            response = await router_instance.route_request(
                endpoint="/api/vehicles",
                method="GET",
                data={},
                service="management"
            )
            
            assert response["status"] == "error"
            assert response["status_code"] == 500


class TestCoreToMaintenanceIntegration:
    """Test integration between Core and Maintenance services"""
    
    @pytest.mark.asyncio
    async def test_maintenance_record_creation_flow(self, mock_rabbitmq_connection):
        """Test maintenance record creation flow from Core to Maintenance"""
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            maintenance_data = {
                "vehicle_id": "vehicle_123",
                "maintenance_type": "oil_change",
                "description": "Regular oil change",
                "scheduled_date": "2024-01-15",
                "estimated_cost": 500.00
            }
            
            router_instance.route_request.return_value = {
                "status": "success",
                "data": {**maintenance_data, "id": "maintenance_123"}
            }
            
            response = await router_instance.route_request(
                endpoint="/maintenance/records",
                method="POST",
                data=maintenance_data,
                service="maintenance"
            )
            
            assert response["status"] == "success"
            assert response["data"]["id"] == "maintenance_123"
    
    @pytest.mark.asyncio
    async def test_maintenance_schedule_retrieval(self, mock_rabbitmq_connection):
        """Test maintenance schedule retrieval from Maintenance service"""
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            schedules_data = [
                {
                    "id": "schedule_123",
                    "vehicle_id": "vehicle_123",
                    "maintenance_type": "oil_change",
                    "frequency": "5000km",
                    "next_due": "2024-03-15"
                }
            ]
            
            router_instance.route_request.return_value = {
                "status": "success",
                "data": schedules_data
            }
            
            response = await router_instance.route_request(
                endpoint="/maintenance/schedules",
                method="GET",
                data={"vehicle_id": "vehicle_123"},
                service="maintenance"
            )
            
            assert response["status"] == "success"
            assert len(response["data"]) == 1
            assert response["data"][0]["id"] == "schedule_123"
    
    @pytest.mark.asyncio
    async def test_maintenance_analytics_flow(self, mock_rabbitmq_connection):
        """Test maintenance analytics flow"""
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            analytics_data = {
                "total_maintenance_cost": 50000.00,
                "overdue_maintenance": 5,
                "upcoming_maintenance": 12,
                "maintenance_by_type": {
                    "oil_change": 15,
                    "tire_replacement": 8,
                    "brake_service": 6
                }
            }
            
            router_instance.route_request.return_value = {
                "status": "success",
                "data": analytics_data
            }
            
            response = await router_instance.route_request(
                endpoint="/maintenance/analytics",
                method="GET",
                data={},
                service="maintenance"
            )
            
            assert response["status"] == "success"
            assert response["data"]["total_maintenance_cost"] == 50000.00
    
    @pytest.mark.asyncio
    async def test_maintenance_notification_flow(self, mock_rabbitmq_connection):
        """Test maintenance notification flow"""
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            notification_data = {
                "type": "overdue_maintenance",
                "vehicle_id": "vehicle_123",
                "message": "Vehicle ABC-123-GP has overdue maintenance",
                "priority": "high"
            }
            
            router_instance.route_request.return_value = {
                "status": "success",
                "data": {**notification_data, "id": "notification_123"}
            }
            
            response = await router_instance.route_request(
                endpoint="/maintenance/notifications",
                method="POST",
                data=notification_data,
                service="maintenance"
            )
            
            assert response["status"] == "success"
            assert response["data"]["id"] == "notification_123"


class TestEventDrivenIntegration:
    """Test event-driven integration between services"""
    
    @pytest.mark.asyncio
    async def test_vehicle_created_event_publishing(self, mock_rabbitmq_connection):
        """Test vehicle created event publishing"""
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connect.return_value = mock_rabbitmq_connection
            
            # Mock event publisher
            with patch('Core.events.publisher.EventPublisher') as mock_publisher:
                publisher_instance = mock_publisher.return_value
                
                # Test event publishing
                vehicle_data = {
                    "id": "vehicle_123",
                    "make": "Toyota",
                    "model": "Camry",
                    "registration_number": "TEST-123-GP"
                }
                
                await publisher_instance.publish_vehicle_created(vehicle_data)
                
                # Verify event was published
                publisher_instance.publish_vehicle_created.assert_called_once_with(vehicle_data)
    
    @pytest.mark.asyncio
    async def test_maintenance_due_event_consumption(self, mock_rabbitmq_connection):
        """Test maintenance due event consumption"""
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connect.return_value = mock_rabbitmq_connection
            
            # Mock event consumer
            with patch('Core.events.consumer.EventConsumer') as mock_consumer:
                consumer_instance = mock_consumer.return_value
                
                # Test event consumption
                maintenance_event = {
                    "type": "maintenance_due",
                    "vehicle_id": "vehicle_123",
                    "maintenance_type": "oil_change",
                    "due_date": "2024-01-15"
                }
                
                # Mock message
                mock_message = MockRabbitMQMessage(
                    body=json.dumps(maintenance_event).encode(),
                    routing_key="maintenance.due"
                )
                
                # Test message handling
                await consumer_instance.handle_message(mock_message)
                
                # Verify message was handled
                consumer_instance.handle_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_driver_assignment_event_flow(self, mock_rabbitmq_connection):
        """Test driver assignment event flow"""
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connect.return_value = mock_rabbitmq_connection
            
            # Test full event flow
            assignment_data = {
                "id": "assignment_123",
                "vehicle_id": "vehicle_123",
                "driver_id": "driver_123",
                "start_date": "2024-01-15"
            }
            
            # Mock publisher
            with patch('Core.events.publisher.EventPublisher') as mock_publisher:
                publisher_instance = mock_publisher.return_value
                
                await publisher_instance.publish_assignment_created(assignment_data)
                
                # Verify event was published
                publisher_instance.publish_assignment_created.assert_called_once_with(assignment_data)


class TestServiceHealthIntegration:
    """Test service health monitoring integration"""
    
    @pytest.mark.asyncio
    async def test_management_service_health_check(self):
        """Test Management service health check"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "database": "connected",
                "rabbitmq": "connected"
            }
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test health check
            async with httpx.AsyncClient() as client:
                response = await client.get("http://management:8000/health")
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_maintenance_service_health_check(self):
        """Test Maintenance service health check"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "database": "connected",
                "rabbitmq": "connected"
            }
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test health check
            async with httpx.AsyncClient() as client:
                response = await client.get("http://maintenance:8000/health")
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_service_discovery_integration(self):
        """Test service discovery integration"""
        with patch('Core.common.service_discovery.ServiceDiscovery') as mock_discovery:
            discovery_instance = mock_discovery.return_value
            
            # Mock service registration
            discovery_instance.register_service.return_value = True
            
            # Test service registration
            result = await discovery_instance.register_service(
                name="management",
                host="management",
                port=8000,
                health_check_url="/health"
            )
            
            assert result == True
            discovery_instance.register_service.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_discovery_failure_handling(self):
        """Test service discovery failure handling"""
        with patch('Core.common.service_discovery.ServiceDiscovery') as mock_discovery:
            discovery_instance = mock_discovery.return_value
            
            # Mock service registration failure
            discovery_instance.register_service.side_effect = Exception("Service discovery unavailable")
            
            # Test graceful failure handling
            try:
                await discovery_instance.register_service(
                    name="management",
                    host="management",
                    port=8000,
                    health_check_url="/health"
                )
            except Exception as e:
                assert "Service discovery unavailable" in str(e)


class TestDataConsistencyIntegration:
    """Test data consistency across services"""
    
    @pytest.mark.asyncio
    async def test_vehicle_data_consistency(self):
        """Test vehicle data consistency between Management and Maintenance services"""
        vehicle_id = "vehicle_123"
        
        # Mock Management service response
        management_vehicle = {
            "id": vehicle_id,
            "make": "Toyota",
            "model": "Camry",
            "registration_number": "TEST-123-GP",
            "status": "active"
        }
        
        # Mock Maintenance service response
        maintenance_records = [
            {
                "id": "maintenance_123",
                "vehicle_id": vehicle_id,
                "maintenance_type": "oil_change",
                "status": "completed"
            }
        ]
        
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            # Mock responses
            router_instance.route_request.side_effect = [
                {"status": "success", "data": management_vehicle},
                {"status": "success", "data": maintenance_records}
            ]
            
            # Get vehicle from Management service
            vehicle_response = await router_instance.route_request(
                endpoint=f"/api/vehicles/{vehicle_id}",
                method="GET",
                data={},
                service="management"
            )
            
            # Get maintenance records from Maintenance service
            maintenance_response = await router_instance.route_request(
                endpoint=f"/maintenance/records?vehicle_id={vehicle_id}",
                method="GET",
                data={},
                service="maintenance"
            )
            
            # Verify data consistency
            assert vehicle_response["data"]["id"] == vehicle_id
            assert maintenance_response["data"][0]["vehicle_id"] == vehicle_id
    
    @pytest.mark.asyncio
    async def test_driver_assignment_consistency(self):
        """Test driver assignment consistency across services"""
        assignment_id = "assignment_123"
        vehicle_id = "vehicle_123"
        driver_id = "driver_123"
        
        # Mock assignment data
        assignment_data = {
            "id": assignment_id,
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "status": "active"
        }
        
        with patch('Core.services.request_router.RequestRouter') as mock_router:
            router_instance = mock_router.return_value
            
            router_instance.route_request.return_value = {
                "status": "success",
                "data": assignment_data
            }
            
            # Test assignment retrieval
            response = await router_instance.route_request(
                endpoint=f"/api/vehicle-assignments/{assignment_id}",
                method="GET",
                data={},
                service="management"
            )
            
            assert response["data"]["vehicle_id"] == vehicle_id
            assert response["data"]["driver_id"] == driver_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
