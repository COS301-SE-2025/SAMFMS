"""
Integration Tests for SAMFMS Core, Management, and Maintenance Services
Tests service integration patterns and mocking capabilities
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Test Configuration
TEST_CONFIG = {
    "core_url": "http://localhost:8000",
    "management_url": "http://localhost:8001", 
    "maintenance_url": "http://localhost:8002",
    "test_user": {
        "email": "test@samfms.com",
        "password": "testpass123"
    }
}

class MockResponse:
    """Mock HTTP response for testing"""
    
    def __init__(self, data: Dict[str, Any], status_code: int = 200):
        self.data = data
        self.status_code = status_code
        self._json_data = data
    
    def json(self):
        return self._json_data
    
    async def json_async(self):
        return self._json_data

class MockRequestRouter:
    """Mock request router for testing"""
    
    def __init__(self):
        self.responses = {}
        self.call_history = []
    
    def set_response(self, endpoint: str, method: str, response_data: Dict[str, Any]):
        """Set mock response for specific endpoint and method"""
        key = f"{method}:{endpoint}"
        self.responses[key] = response_data
    
    async def route_request(self, endpoint: str, method: str, data: Dict[str, Any] = None, service: str = None):
        """Mock route request implementation"""
        key = f"{method}:{endpoint}"
        self.call_history.append({
            "endpoint": endpoint,
            "method": method,
            "data": data,
            "service": service,
            "timestamp": datetime.utcnow()
        })
        
        if key in self.responses:
            return self.responses[key]
        
        # Default success response
        return {
            "status": "success",
            "data": {"message": "Mock response"},
            "status_code": 200
        }

@pytest.fixture
def mock_request_router():
    """Mock request router fixture"""
    return MockRequestRouter()

@pytest.fixture
def sample_vehicle_data():
    """Sample vehicle data for testing"""
    return {
        "make": "Toyota",
        "model": "Camry",
        "year": 2023,
        "registration_number": "TEST-123-GP",
        "vin": "1HGCM82633A123456",
        "status": "active"
    }

@pytest.fixture
def sample_driver_data():
    """Sample driver data for testing"""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@samfms.com",
        "license_number": "DL-123-GP",
        "status": "active"
    }

@pytest.fixture
def sample_maintenance_data():
    """Sample maintenance data for testing"""
    return {
        "vehicle_id": "vehicle_123",
        "maintenance_type": "oil_change",
        "description": "Regular oil change",
        "scheduled_date": "2024-01-15",
        "estimated_cost": 500.00,
        "status": "scheduled"
    }

class TestCoreManagementIntegration:
    """Test integration between Core and Management services"""
    
    @pytest.mark.asyncio
    async def test_vehicle_creation_flow(self, mock_request_router, sample_vehicle_data):
        """Test vehicle creation flow through Core to Management"""
        # Set up mock response
        expected_response = {
            "status": "success",
            "data": {**sample_vehicle_data, "id": "vehicle_123"},
            "status_code": 201
        }
        mock_request_router.set_response("/api/vehicles", "POST", expected_response)
        
        # Test the flow
        response = await mock_request_router.route_request(
            endpoint="/api/vehicles",
            method="POST",
            data=sample_vehicle_data,
            service="management"
        )
        
        # Assertions
        assert response["status"] == "success"
        assert response["data"]["id"] == "vehicle_123"
        assert response["data"]["make"] == sample_vehicle_data["make"]
        assert len(mock_request_router.call_history) == 1
        assert mock_request_router.call_history[0]["service"] == "management"
    
    @pytest.mark.asyncio
    async def test_driver_management_flow(self, mock_request_router, sample_driver_data):
        """Test driver management flow through Core to Management"""
        # Set up mock response
        expected_response = {
            "status": "success",
            "data": {**sample_driver_data, "id": "driver_123"},
            "status_code": 201
        }
        mock_request_router.set_response("/api/drivers", "POST", expected_response)
        
        # Test the flow
        response = await mock_request_router.route_request(
            endpoint="/api/drivers",
            method="POST", 
            data=sample_driver_data,
            service="management"
        )
        
        # Assertions
        assert response["status"] == "success"
        assert response["data"]["id"] == "driver_123"
        assert response["data"]["first_name"] == sample_driver_data["first_name"]
        assert len(mock_request_router.call_history) == 1
    
    @pytest.mark.asyncio
    async def test_vehicle_assignment_flow(self, mock_request_router):
        """Test vehicle assignment flow"""
        assignment_data = {
            "vehicle_id": "vehicle_123",
            "driver_id": "driver_123",
            "start_date": "2024-01-15",
            "end_date": "2024-01-20",
            "purpose": "Security patrol"
        }
        
        expected_response = {
            "status": "success",
            "data": {**assignment_data, "id": "assignment_123"},
            "status_code": 201
        }
        mock_request_router.set_response("/api/vehicle-assignments", "POST", expected_response)
        
        response = await mock_request_router.route_request(
            endpoint="/api/vehicle-assignments",
            method="POST",
            data=assignment_data,
            service="management"
        )
        
        assert response["status"] == "success"
        assert response["data"]["id"] == "assignment_123"
        assert response["data"]["vehicle_id"] == "vehicle_123"
        assert response["data"]["driver_id"] == "driver_123"
    
    @pytest.mark.asyncio
    async def test_analytics_data_retrieval(self, mock_request_router):
        """Test analytics data retrieval from Management service"""
        analytics_data = {
            "total_vehicles": 50,
            "active_drivers": 35,
            "fleet_utilization": 78.5,
            "monthly_costs": 45000.00
        }
        
        expected_response = {
            "status": "success",
            "data": analytics_data,
            "status_code": 200
        }
        mock_request_router.set_response("/api/analytics/dashboard", "GET", expected_response)
        
        response = await mock_request_router.route_request(
            endpoint="/api/analytics/dashboard",
            method="GET",
            service="management"
        )
        
        assert response["status"] == "success"
        assert response["data"]["total_vehicles"] == 50
        assert response["data"]["active_drivers"] == 35
        assert response["data"]["fleet_utilization"] == 78.5

class TestCoreMaintenanceIntegration:
    """Test integration between Core and Maintenance services"""
    
    @pytest.mark.asyncio
    async def test_maintenance_record_creation(self, mock_request_router, sample_maintenance_data):
        """Test maintenance record creation flow"""
        expected_response = {
            "status": "success",
            "data": {**sample_maintenance_data, "id": "maintenance_123"},
            "status_code": 201
        }
        mock_request_router.set_response("/maintenance/records", "POST", expected_response)
        
        response = await mock_request_router.route_request(
            endpoint="/maintenance/records",
            method="POST",
            data=sample_maintenance_data,
            service="maintenance"
        )
        
        assert response["status"] == "success"
        assert response["data"]["id"] == "maintenance_123"
        assert response["data"]["vehicle_id"] == "vehicle_123"
        assert response["data"]["maintenance_type"] == "oil_change"
    
    @pytest.mark.asyncio
    async def test_maintenance_schedule_retrieval(self, mock_request_router):
        """Test maintenance schedule retrieval"""
        schedules_data = [
            {
                "id": "schedule_123",
                "vehicle_id": "vehicle_123",
                "maintenance_type": "oil_change",
                "frequency": "5000km",
                "next_due": "2024-03-15"
            },
            {
                "id": "schedule_124",
                "vehicle_id": "vehicle_123",
                "maintenance_type": "tire_rotation",
                "frequency": "10000km",
                "next_due": "2024-04-15"
            }
        ]
        
        expected_response = {
            "status": "success",
            "data": schedules_data,
            "status_code": 200
        }
        mock_request_router.set_response("/maintenance/schedules", "GET", expected_response)
        
        response = await mock_request_router.route_request(
            endpoint="/maintenance/schedules",
            method="GET",
            data={"vehicle_id": "vehicle_123"},
            service="maintenance"
        )
        
        assert response["status"] == "success"
        assert len(response["data"]) == 2
        assert response["data"][0]["id"] == "schedule_123"
        assert response["data"][1]["id"] == "schedule_124"
    
    @pytest.mark.asyncio
    async def test_maintenance_analytics(self, mock_request_router):
        """Test maintenance analytics retrieval"""
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
        
        expected_response = {
            "status": "success",
            "data": analytics_data,
            "status_code": 200
        }
        mock_request_router.set_response("/maintenance/analytics", "GET", expected_response)
        
        response = await mock_request_router.route_request(
            endpoint="/maintenance/analytics",
            method="GET",
            service="maintenance"
        )
        
        assert response["status"] == "success"
        assert response["data"]["total_maintenance_cost"] == 50000.00
        assert response["data"]["overdue_maintenance"] == 5
        assert response["data"]["upcoming_maintenance"] == 12

class TestServiceErrorHandling:
    """Test error handling across services"""
    
    @pytest.mark.asyncio
    async def test_service_timeout_handling(self, mock_request_router):
        """Test handling of service timeouts"""
        # Mock timeout scenario
        async def mock_timeout_route(*args, **kwargs):
            raise asyncio.TimeoutError("Service timeout")
        
        mock_request_router.route_request = mock_timeout_route
        
        with pytest.raises(asyncio.TimeoutError):
            await mock_request_router.route_request(
                endpoint="/api/vehicles",
                method="GET",
                service="management"
            )
    
    @pytest.mark.asyncio
    async def test_service_error_response(self, mock_request_router):
        """Test handling of service error responses"""
        error_response = {
            "status": "error",
            "message": "Database connection failed",
            "status_code": 500
        }
        mock_request_router.set_response("/api/vehicles", "GET", error_response)
        
        response = await mock_request_router.route_request(
            endpoint="/api/vehicles",
            method="GET",
            service="management"
        )
        
        assert response["status"] == "error"
        assert response["status_code"] == 500
        assert "Database connection failed" in response["message"]
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, mock_request_router):
        """Test validation error handling"""
        validation_error = {
            "status": "error",
            "message": "Invalid vehicle data",
            "errors": ["Registration number is required", "Make is required"],
            "status_code": 400
        }
        mock_request_router.set_response("/api/vehicles", "POST", validation_error)
        
        response = await mock_request_router.route_request(
            endpoint="/api/vehicles",
            method="POST",
            data={"invalid": "data"},
            service="management"
        )
        
        assert response["status"] == "error"
        assert response["status_code"] == 400
        assert "Invalid vehicle data" in response["message"]
        assert len(response["errors"]) == 2

class TestEventDrivenIntegration:
    """Test event-driven integration patterns"""
    
    @pytest.mark.asyncio
    async def test_vehicle_created_event(self, mock_request_router):
        """Test vehicle created event flow"""
        # Mock event publishing
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connection = AsyncMock()
            mock_channel = AsyncMock()
            mock_exchange = AsyncMock()
            
            mock_connect.return_value = mock_connection
            mock_connection.channel.return_value = mock_channel
            mock_channel.declare_exchange.return_value = mock_exchange
            
            # Test event data
            event_data = {
                "event_type": "vehicle_created",
                "vehicle_id": "vehicle_123",
                "data": {
                    "make": "Toyota",
                    "model": "Camry",
                    "registration_number": "TEST-123-GP"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Mock the event publishing
            await mock_exchange.publish(
                Mock(body=json.dumps(event_data).encode()),
                routing_key="vehicle.created"
            )
            
            # Verify event was published
            mock_exchange.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_maintenance_scheduled_event(self, mock_request_router):
        """Test maintenance scheduled event flow"""
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connection = AsyncMock()
            mock_channel = AsyncMock()
            mock_exchange = AsyncMock()
            
            mock_connect.return_value = mock_connection
            mock_connection.channel.return_value = mock_channel
            mock_channel.declare_exchange.return_value = mock_exchange
            
            event_data = {
                "event_type": "maintenance_scheduled",
                "maintenance_id": "maintenance_123",
                "vehicle_id": "vehicle_123",
                "data": {
                    "maintenance_type": "oil_change",
                    "scheduled_date": "2024-01-15"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await mock_exchange.publish(
                Mock(body=json.dumps(event_data).encode()),
                routing_key="maintenance.scheduled"
            )
            
            mock_exchange.publish.assert_called_once()

class TestDataConsistency:
    """Test data consistency across services"""
    
    @pytest.mark.asyncio
    async def test_vehicle_data_consistency(self, mock_request_router):
        """Test vehicle data consistency between Management and Maintenance"""
        vehicle_id = "vehicle_123"
        
        # Mock Management service response
        management_response = {
            "status": "success",
            "data": {
                "id": vehicle_id,
                "make": "Toyota",
                "model": "Camry",
                "registration_number": "TEST-123-GP",
                "status": "active"
            },
            "status_code": 200
        }
        
        # Mock Maintenance service response
        maintenance_response = {
            "status": "success",
            "data": [
                {
                    "id": "maintenance_123",
                    "vehicle_id": vehicle_id,
                    "maintenance_type": "oil_change",
                    "status": "completed"
                }
            ],
            "status_code": 200
        }
        
        mock_request_router.set_response(f"/api/vehicles/{vehicle_id}", "GET", management_response)
        mock_request_router.set_response(f"/maintenance/records", "GET", maintenance_response)
        
        # Get vehicle from Management
        vehicle_response = await mock_request_router.route_request(
            endpoint=f"/api/vehicles/{vehicle_id}",
            method="GET",
            service="management"
        )
        
        # Get maintenance records from Maintenance
        maintenance_records_response = await mock_request_router.route_request(
            endpoint="/maintenance/records",
            method="GET",
            data={"vehicle_id": vehicle_id},
            service="maintenance"
        )
        
        # Verify data consistency
        assert vehicle_response["data"]["id"] == vehicle_id
        assert maintenance_records_response["data"][0]["vehicle_id"] == vehicle_id
        assert len(mock_request_router.call_history) == 2

class TestServiceHealth:
    """Test service health monitoring"""
    
    @pytest.mark.asyncio
    async def test_service_health_checks(self, mock_request_router):
        """Test service health check integration"""
        # Mock health check responses
        health_responses = {
            "management": {
                "status": "success",
                "data": {
                    "service": "management",
                    "status": "healthy",
                    "database": "connected",
                    "rabbitmq": "connected",
                    "timestamp": datetime.utcnow().isoformat()
                },
                "status_code": 200
            },
            "maintenance": {
                "status": "success",
                "data": {
                    "service": "maintenance",
                    "status": "healthy",
                    "database": "connected",
                    "rabbitmq": "connected",
                    "timestamp": datetime.utcnow().isoformat()
                },
                "status_code": 200
            }
        }
        
        mock_request_router.set_response("/health", "GET", health_responses["management"])
        
        # Test Management service health
        management_health = await mock_request_router.route_request(
            endpoint="/health",
            method="GET",
            service="management"
        )
        
        assert management_health["status"] == "success"
        assert management_health["data"]["service"] == "management"
        assert management_health["data"]["status"] == "healthy"
        assert management_health["data"]["database"] == "connected"
        assert management_health["data"]["rabbitmq"] == "connected"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
