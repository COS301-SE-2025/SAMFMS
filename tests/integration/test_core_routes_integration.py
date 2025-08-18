"""
Comprehensive Integration Tests for SAMFMS Core Routes
Tests integration between Core, Management, and Maintenance services
"""

import pytest
import asyncio
import httpx
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestConfig:
    """Test configuration"""
    CORE_BASE_URL = "http://localhost:8000"
    MANAGEMENT_BASE_URL = "http://localhost:8001"
    MAINTENANCE_BASE_URL = "http://localhost:8002"
    SECURITY_BASE_URL = "http://localhost:8003"
    
    # Test credentials
    TEST_USER_EMAIL = "test@samfms.com"
    TEST_USER_PASSWORD = "testpass123"
    TEST_ADMIN_EMAIL = "admin@samfms.com"
    TEST_ADMIN_PASSWORD = "adminpass123"


class MockServiceResponse:
    """Mock service response helper"""
    
    @staticmethod
    def success_response(data: Dict[str, Any], status_code: int = 200):
        """Create a successful response"""
        return {
            "status": "success",
            "data": data,
            "status_code": status_code
        }
    
    @staticmethod
    def error_response(message: str, status_code: int = 400):
        """Create an error response"""
        return {
            "status": "error",
            "message": message,
            "status_code": status_code
        }


@pytest.fixture
async def auth_token():
    """Mock authentication token for testing"""
    return "mock_jwt_token_for_testing"


@pytest.fixture
async def test_client():
    """Test client for making HTTP requests"""
    async with httpx.AsyncClient(base_url=TestConfig.CORE_BASE_URL) as client:
        yield client


@pytest.fixture
def mock_vehicle_data():
    """Mock vehicle data for testing"""
    return {
        "make": "Toyota",
        "model": "Camry",
        "year": 2023,
        "registration_number": "ABC-123-GP",
        "license_plate": "ABC-123-GP",
        "vin": "1HGCM82633A123456",
        "color": "Silver",
        "department": "Security",
        "status": "available",
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "engine_capacity": "2.5L",
        "purchase_date": "2023-01-15",
        "mileage": 15000,
        "insurance_expiry": "2024-12-31",
        "license_expiry": "2025-01-15"
    }


@pytest.fixture
def mock_driver_data():
    """Mock driver data for testing"""
    return {
        "employee_id": "EMP001",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@samfms.com",
        "phone": "+27123456789",
        "license_number": "DL123456789",
        "license_expiry": "2025-06-30",
        "department": "Security",
        "status": "active",
        "hire_date": "2023-01-15",
        "birth_date": "1990-05-15",
        "address": "123 Main St, Cape Town",
        "emergency_contact": "Jane Doe: +27987654321"
    }


@pytest.fixture
def mock_maintenance_data():
    """Mock maintenance data for testing"""
    return {
        "vehicle_id": "vehicle_123",
        "maintenance_type": "regular_service",
        "description": "Regular 15000km service",
        "scheduled_date": "2024-01-15",
        "estimated_cost": 1500.00,
        "priority": "medium",
        "vendor": "Toyota Service Center",
        "notes": "Check brakes and replace oil filter"
    }


class TestCoreAuthRoutes:
    """Test Core authentication routes"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_client):
        """Test successful login"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "access_token": "mock_token",
                "token_type": "bearer",
                "user_id": "user123",
                "role": "admin",
                "permissions": ["read", "write"],
                "preferences": {}
            }
            
            response = await test_client.post("/auth/login", json={
                "email": TestConfig.TEST_USER_EMAIL,
                "password": TestConfig.TEST_USER_PASSWORD
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert data["user_id"] == "user123"
    
    @pytest.mark.asyncio
    async def test_login_failure(self, test_client):
        """Test failed login"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 401
            mock_post.return_value.json.return_value = {
                "detail": "Invalid credentials"
            }
            
            response = await test_client.post("/auth/login", json={
                "email": TestConfig.TEST_USER_EMAIL,
                "password": "wrong_password"
            })
            
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_signup_success(self, test_client):
        """Test successful signup"""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "access_token": "mock_token",
                "token_type": "bearer",
                "user_id": "user123",
                "role": "user",
                "permissions": ["read"],
                "preferences": {}
            }
            
            response = await test_client.post("/auth/signup", json={
                "full_name": "Test User",
                "email": "newuser@samfms.com",
                "password": "newpassword123",
                "role": "user"
            })
            
            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_security_service_unavailable(self, test_client):
        """Test handling when security service is unavailable"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.RequestException("Connection failed")
            
            response = await test_client.post("/auth/login", json={
                "email": TestConfig.TEST_USER_EMAIL,
                "password": TestConfig.TEST_USER_PASSWORD
            })
            
            assert response.status_code == 503
            assert "Security service unavailable" in response.json()["detail"]


class TestCoreVehicleRoutes:
    """Test Core vehicle routes integration with Management service"""
    
    @pytest.mark.asyncio
    async def test_get_vehicles_success(self, test_client, auth_token, mock_vehicle_data):
        """Test successful vehicle retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.return_value = MockServiceResponse.success_response([mock_vehicle_data])
            
            response = await test_client.get(
                "/api/vehicles",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) >= 1
    
    @pytest.mark.asyncio
    async def test_create_vehicle_success(self, test_client, auth_token, mock_vehicle_data):
        """Test successful vehicle creation"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            created_vehicle = {**mock_vehicle_data, "id": "vehicle_123"}
            mock_request.return_value = MockServiceResponse.success_response(created_vehicle, 201)
            
            response = await test_client.post(
                "/api/vehicles",
                json=mock_vehicle_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["id"] == "vehicle_123"
    
    @pytest.mark.asyncio
    async def test_create_vehicle_validation_error(self, test_client, auth_token):
        """Test vehicle creation with validation errors"""
        invalid_data = {
            "make": "Toyota",
            # Missing required fields
        }
        
        with patch('Core.routes.api.base.validate_required_fields') as mock_validate:
            mock_validate.side_effect = ValueError("Missing required fields")
            
            response = await test_client.post(
                "/api/vehicles",
                json=invalid_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_update_vehicle_success(self, test_client, auth_token):
        """Test successful vehicle update"""
        vehicle_id = "vehicle_123"
        update_data = {"mileage": 20000, "status": "in_use"}
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            updated_vehicle = {"id": vehicle_id, **update_data}
            mock_request.return_value = MockServiceResponse.success_response(updated_vehicle)
            
            response = await test_client.put(
                f"/api/vehicles/{vehicle_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["mileage"] == 20000
    
    @pytest.mark.asyncio
    async def test_delete_vehicle_success(self, test_client, auth_token):
        """Test successful vehicle deletion"""
        vehicle_id = "vehicle_123"
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.return_value = MockServiceResponse.success_response({"deleted": True})
            
            response = await test_client.delete(
                f"/api/vehicles/{vehicle_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["deleted"] == True
    
    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_not_found(self, test_client, auth_token):
        """Test getting non-existent vehicle"""
        vehicle_id = "nonexistent_vehicle"
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.return_value = MockServiceResponse.error_response("Vehicle not found", 404)
            
            response = await test_client.get(
                f"/api/vehicles/{vehicle_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 404


class TestCoreDriverRoutes:
    """Test Core driver routes integration with Management service"""
    
    @pytest.mark.asyncio
    async def test_get_drivers_success(self, test_client, auth_token, mock_driver_data):
        """Test successful driver retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.return_value = MockServiceResponse.success_response([mock_driver_data])
            
            response = await test_client.get(
                "/api/drivers",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) >= 1
    
    @pytest.mark.asyncio
    async def test_create_driver_success(self, test_client, auth_token, mock_driver_data):
        """Test successful driver creation"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            created_driver = {**mock_driver_data, "id": "driver_123"}
            mock_request.return_value = MockServiceResponse.success_response(created_driver, 201)
            
            response = await test_client.post(
                "/api/drivers",
                json=mock_driver_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["id"] == "driver_123"
    
    @pytest.mark.asyncio
    async def test_get_driver_by_id_success(self, test_client, auth_token, mock_driver_data):
        """Test successful driver retrieval by ID"""
        driver_id = "driver_123"
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            driver_with_id = {**mock_driver_data, "id": driver_id}
            mock_request.return_value = MockServiceResponse.success_response(driver_with_id)
            
            response = await test_client.get(
                f"/api/drivers/{driver_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["id"] == driver_id
    
    @pytest.mark.asyncio
    async def test_update_driver_success(self, test_client, auth_token):
        """Test successful driver update"""
        driver_id = "driver_123"
        update_data = {"phone": "+27111222333", "status": "inactive"}
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            updated_driver = {"id": driver_id, **update_data}
            mock_request.return_value = MockServiceResponse.success_response(updated_driver)
            
            response = await test_client.put(
                f"/api/drivers/{driver_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["phone"] == "+27111222333"


class TestCoreMaintenanceRoutes:
    """Test Core maintenance routes integration with Maintenance service"""
    
    @pytest.mark.asyncio
    async def test_get_maintenance_records_success(self, test_client, auth_token, mock_maintenance_data):
        """Test successful maintenance records retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.return_value = MockServiceResponse.success_response([mock_maintenance_data])
            
            response = await test_client.get(
                "/api/maintenance/records",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) >= 1
    
    @pytest.mark.asyncio
    async def test_create_maintenance_record_success(self, test_client, auth_token, mock_maintenance_data):
        """Test successful maintenance record creation"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            created_record = {**mock_maintenance_data, "id": "maintenance_123"}
            mock_request.return_value = MockServiceResponse.success_response(created_record, 201)
            
            response = await test_client.post(
                "/api/maintenance/records",
                json=mock_maintenance_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["id"] == "maintenance_123"
    
    @pytest.mark.asyncio
    async def test_get_maintenance_schedules_success(self, test_client, auth_token):
        """Test successful maintenance schedules retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_schedules = [
                {
                    "id": "schedule_123",
                    "vehicle_id": "vehicle_123",
                    "maintenance_type": "oil_change",
                    "frequency": "5000km",
                    "next_due": "2024-03-15"
                }
            ]
            mock_request.return_value = MockServiceResponse.success_response(mock_schedules)
            
            response = await test_client.get(
                "/api/maintenance/schedules",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_maintenance_analytics_success(self, test_client, auth_token):
        """Test successful maintenance analytics retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_analytics = {
                "total_maintenance_cost": 50000.00,
                "overdue_maintenance": 5,
                "upcoming_maintenance": 12,
                "maintenance_by_type": {
                    "oil_change": 15,
                    "tire_replacement": 8,
                    "brake_service": 6
                }
            }
            mock_request.return_value = MockServiceResponse.success_response(mock_analytics)
            
            response = await test_client.get(
                "/api/maintenance/analytics",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "total_maintenance_cost" in data["data"]
    
    @pytest.mark.asyncio
    async def test_update_maintenance_record_success(self, test_client, auth_token):
        """Test successful maintenance record update"""
        record_id = "maintenance_123"
        update_data = {"status": "completed", "actual_cost": 1600.00}
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            updated_record = {"id": record_id, **update_data}
            mock_request.return_value = MockServiceResponse.success_response(updated_record)
            
            response = await test_client.put(
                f"/api/maintenance/records/{record_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["status"] == "completed"


class TestCoreAnalyticsRoutes:
    """Test Core analytics routes integration with Management service"""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_analytics_success(self, test_client, auth_token):
        """Test successful dashboard analytics retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_analytics = {
                "total_vehicles": 50,
                "active_drivers": 35,
                "fleet_utilization": 78.5,
                "maintenance_due": 8,
                "fuel_consumption": 2500.50,
                "monthly_costs": 45000.00
            }
            mock_request.return_value = MockServiceResponse.success_response(mock_analytics)
            
            response = await test_client.get(
                "/api/analytics/dashboard",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "total_vehicles" in data["data"]
            assert "fleet_utilization" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_fleet_utilization_success(self, test_client, auth_token):
        """Test successful fleet utilization retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_utilization = {
                "overall_utilization": 78.5,
                "by_department": {
                    "Security": 85.2,
                    "Administration": 65.8,
                    "Maintenance": 92.1
                },
                "by_vehicle_type": {
                    "Sedan": 75.3,
                    "SUV": 82.7,
                    "Truck": 88.4
                }
            }
            mock_request.return_value = MockServiceResponse.success_response(mock_utilization)
            
            response = await test_client.get(
                "/api/analytics/fleet-utilization",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "overall_utilization" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_cost_analytics_success(self, test_client, auth_token):
        """Test successful cost analytics retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_costs = {
                "total_monthly_cost": 45000.00,
                "fuel_costs": 18000.00,
                "maintenance_costs": 15000.00,
                "insurance_costs": 8000.00,
                "other_costs": 4000.00,
                "cost_per_vehicle": 900.00,
                "cost_trends": [
                    {"month": "2024-01", "cost": 42000.00},
                    {"month": "2024-02", "cost": 45000.00}
                ]
            }
            mock_request.return_value = MockServiceResponse.success_response(mock_costs)
            
            response = await test_client.get(
                "/api/analytics/costs",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "total_monthly_cost" in data["data"]


class TestCoreAssignmentRoutes:
    """Test Core assignment routes integration with Management service"""
    
    @pytest.mark.asyncio
    async def test_get_vehicle_assignments_success(self, test_client, auth_token):
        """Test successful vehicle assignments retrieval"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_assignments = [
                {
                    "id": "assignment_123",
                    "vehicle_id": "vehicle_123",
                    "driver_id": "driver_123",
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-16",
                    "status": "active",
                    "purpose": "Security patrol"
                }
            ]
            mock_request.return_value = MockServiceResponse.success_response(mock_assignments)
            
            response = await test_client.get(
                "/api/vehicle-assignments",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) >= 1
    
    @pytest.mark.asyncio
    async def test_create_vehicle_assignment_success(self, test_client, auth_token):
        """Test successful vehicle assignment creation"""
        assignment_data = {
            "vehicle_id": "vehicle_123",
            "driver_id": "driver_123",
            "start_date": "2024-01-15",
            "end_date": "2024-01-16",
            "purpose": "Security patrol"
        }
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            created_assignment = {**assignment_data, "id": "assignment_123"}
            mock_request.return_value = MockServiceResponse.success_response(created_assignment, 201)
            
            response = await test_client.post(
                "/api/vehicle-assignments",
                json=assignment_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["id"] == "assignment_123"
    
    @pytest.mark.asyncio
    async def test_update_assignment_status_success(self, test_client, auth_token):
        """Test successful assignment status update"""
        assignment_id = "assignment_123"
        update_data = {"status": "completed"}
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            updated_assignment = {"id": assignment_id, **update_data}
            mock_request.return_value = MockServiceResponse.success_response(updated_assignment)
            
            response = await test_client.put(
                f"/api/vehicle-assignments/{assignment_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["status"] == "completed"


class TestServiceIntegration:
    """Test integration between Core and backend services"""
    
    @pytest.mark.asyncio
    async def test_management_service_unavailable(self, test_client, auth_token):
        """Test handling when Management service is unavailable"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.side_effect = Exception("Management service unavailable")
            
            response = await test_client.get(
                "/api/vehicles",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 503
    
    @pytest.mark.asyncio
    async def test_maintenance_service_unavailable(self, test_client, auth_token):
        """Test handling when Maintenance service is unavailable"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.side_effect = Exception("Maintenance service unavailable")
            
            response = await test_client.get(
                "/api/maintenance/records",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 503
    
    @pytest.mark.asyncio
    async def test_service_timeout_handling(self, test_client, auth_token):
        """Test handling of service timeouts"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.side_effect = asyncio.TimeoutError("Service timeout")
            
            response = await test_client.get(
                "/api/vehicles",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 504
    
    @pytest.mark.asyncio
    async def test_authentication_required(self, test_client):
        """Test that authentication is required for protected routes"""
        response = await test_client.get("/api/vehicles")
        assert response.status_code == 401
        
        response = await test_client.get("/api/drivers")
        assert response.status_code == 401
        
        response = await test_client.get("/api/maintenance/records")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_cross_service_data_consistency(self, test_client, auth_token):
        """Test data consistency across services"""
        # Create a vehicle in Management service
        vehicle_data = {
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "registration_number": "TEST-123-GP"
        }
        
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            # Mock vehicle creation
            created_vehicle = {**vehicle_data, "id": "vehicle_123"}
            mock_request.return_value = MockServiceResponse.success_response(created_vehicle, 201)
            
            vehicle_response = await test_client.post(
                "/api/vehicles",
                json=vehicle_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert vehicle_response.status_code == 201
            vehicle_id = vehicle_response.json()["data"]["id"]
            
            # Create maintenance record for the same vehicle
            maintenance_data = {
                "vehicle_id": vehicle_id,
                "maintenance_type": "oil_change",
                "description": "Regular oil change",
                "scheduled_date": "2024-01-15"
            }
            
            # Mock maintenance record creation
            created_maintenance = {**maintenance_data, "id": "maintenance_123"}
            mock_request.return_value = MockServiceResponse.success_response(created_maintenance, 201)
            
            maintenance_response = await test_client.post(
                "/api/maintenance/records",
                json=maintenance_data,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert maintenance_response.status_code == 201
            assert maintenance_response.json()["data"]["vehicle_id"] == vehicle_id


class TestErrorHandling:
    """Test error handling across all routes"""
    
    @pytest.mark.asyncio
    async def test_invalid_json_request(self, test_client, auth_token):
        """Test handling of invalid JSON requests"""
        response = await test_client.post(
            "/api/vehicles",
            data="invalid json",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, test_client, auth_token):
        """Test handling of missing required fields"""
        incomplete_data = {"make": "Toyota"}  # Missing required fields
        
        response = await test_client.post(
            "/api/vehicles",
            json=incomplete_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_resource_id(self, test_client, auth_token):
        """Test handling of invalid resource IDs"""
        with patch('Core.routes.api.base.handle_service_request') as mock_request:
            mock_request.return_value = MockServiceResponse.error_response("Invalid ID format", 400)
            
            response = await test_client.get(
                "/api/vehicles/invalid-id",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 400


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
