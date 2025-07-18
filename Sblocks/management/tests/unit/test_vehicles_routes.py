"""
Unit tests for vehicles routes
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from api.routes.vehicles import router
from schemas.requests import VehicleCreateRequest, VehicleUpdateRequest
from schemas.responses import StandardResponse

# Create a test app instance
app = FastAPI()
app.include_router(router)


@pytest.mark.unit
@pytest.mark.api
class TestVehiclesRoutes:
    """Test class for vehicles API routes"""
    
    def setup_method(self):
        """Setup test client and dependencies"""
        self.client = TestClient(app)
        self.base_url = "/api/v1/vehicles"
        
        # Mock authentication
        self.mock_user = {
            "user_id": "test_user",
            "role": "manager",
            "permissions": ["vehicles:read", "vehicles:create", "vehicles:update"],
            "department": "operations"
        }
        
        # Mock vehicle data
        self.vehicle_id = str(ObjectId())
        self.mock_vehicle = {
            "_id": self.vehicle_id,
            "registration_number": "ABC-001",
            "license_plate": "ABC001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "color": "White",
            "fuel_type": "petrol",
            "engine_size": 2.0,
            "mileage": 15000,
            "status": "available",
            "department": "operations",
            "acquisition_date": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
    @pytest.mark.asyncio
    async def test_create_vehicle_success(self):
        """Test creating vehicle successfully"""
        # Arrange
        vehicle_data = {
            "registration_number": "XYZ-002",
            "license_plate": "XYZ002",
            "make": "Honda",
            "model": "Civic",
            "year": 2024,
            "color": "Blue",
            "fuel_type": "petrol",
            "engine_size": 1.8,
            "mileage": 0,
            "status": "available",
            "department": "operations",
            "acquisition_date": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.create_vehicle.return_value = self.mock_vehicle
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=vehicle_data)
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["success"] is True
            assert data["data"]["registration_number"] == "ABC-001"  # From mock
            assert data["data"]["make"] == "Toyota"
            mock_service.create_vehicle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_vehicle_invalid_data(self):
        """Test creating vehicle with invalid data"""
        # Arrange
        invalid_data = {
            "registration_number": "",  # Empty registration
            "license_plate": "",  # Empty license plate
            "make": "",  # Empty make
            "model": "",  # Empty model
            "year": 1800,  # Invalid year
            "color": "",  # Empty color
            "fuel_type": "invalid_fuel",  # Invalid fuel type
            "engine_size": -1.0,  # Invalid engine size
            "mileage": -1000,  # Invalid mileage
            "status": "invalid_status",  # Invalid status
            "department": "",  # Empty department
            "acquisition_date": "invalid_date"  # Invalid date format
        }
        
        with patch('api.routes.vehicles.get_current_user') as mock_auth:
            mock_auth.return_value = self.mock_user
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=invalid_data)
            
            # Assert
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_get_vehicle_success(self):
        """Test getting vehicle by ID successfully"""
        # Arrange
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicle_by_id.return_value = self.mock_vehicle
            
            # Act
            response = self.client.get(f"{self.base_url}/{self.vehicle_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["_id"] == self.vehicle_id
            assert data["data"]["registration_number"] == "ABC-001"
            mock_service.get_vehicle_by_id.assert_called_once_with(self.vehicle_id)
    
    @pytest.mark.asyncio
    async def test_get_vehicle_not_found(self):
        """Test getting vehicle that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicle_by_id.return_value = None
            
            # Act
            response = self.client.get(f"{self.base_url}/{nonexistent_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_get_vehicles_list_success(self):
        """Test getting vehicles list successfully"""
        # Arrange
        mock_vehicles = [
            self.mock_vehicle,
            {
                "_id": str(ObjectId()),
                "registration_number": "DEF-003",
                "license_plate": "DEF003",
                "make": "Ford",
                "model": "Focus",
                "year": 2022,
                "color": "Red",
                "fuel_type": "diesel",
                "status": "in_use",
                "department": "maintenance",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicles.return_value = mock_vehicles
            
            # Act
            response = self.client.get(f"{self.base_url}/")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["data"][0]["registration_number"] == "ABC-001"
            assert data["data"][1]["registration_number"] == "DEF-003"
            mock_service.get_vehicles.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_vehicles_with_filters(self):
        """Test getting vehicles list with filters"""
        # Arrange
        filtered_vehicles = [self.mock_vehicle]
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicles.return_value = filtered_vehicles
            
            # Act
            response = self.client.get(f"{self.base_url}/?status=available&fuel_type=petrol")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["status"] == "available"
            assert data["data"][0]["fuel_type"] == "petrol"
            mock_service.get_vehicles.assert_called_once_with(
                status="available",
                fuel_type="petrol"
            )
    
    @pytest.mark.asyncio
    async def test_get_vehicles_with_pagination(self):
        """Test getting vehicles list with pagination"""
        # Arrange
        mock_vehicles = [self.mock_vehicle]
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicles.return_value = mock_vehicles
            
            # Act
            response = self.client.get(f"{self.base_url}/?page=1&page_size=10")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            mock_service.get_vehicles.assert_called_once_with(
                page=1,
                page_size=10
            )
    
    @pytest.mark.asyncio
    async def test_update_vehicle_success(self):
        """Test updating vehicle successfully"""
        # Arrange
        update_data = {
            "mileage": 16000,
            "status": "maintenance",
            "color": "Silver"
        }
        
        updated_vehicle = {
            **self.mock_vehicle,
            **update_data,
            "updated_at": datetime.now(timezone.utc)
        }
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.update_vehicle.return_value = updated_vehicle
            
            # Act
            response = self.client.put(f"{self.base_url}/{self.vehicle_id}", json=update_data)
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["mileage"] == 16000
            assert data["data"]["status"] == "maintenance"
            mock_service.update_vehicle.assert_called_once_with(
                self.vehicle_id,
                update_data,
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self):
        """Test updating vehicle that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        update_data = {"mileage": 16000}
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.update_vehicle.return_value = None
            
            # Act
            response = self.client.put(f"{self.base_url}/{nonexistent_id}", json=update_data)
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_vehicle_success(self):
        """Test deleting vehicle successfully"""
        # Arrange
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.delete_vehicle.return_value = True
            
            # Act
            response = self.client.delete(f"{self.base_url}/{self.vehicle_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "deleted" in data["message"].lower()
            mock_service.delete_vehicle.assert_called_once_with(
                self.vehicle_id,
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_delete_vehicle_not_found(self):
        """Test deleting vehicle that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.delete_vehicle.return_value = False
            
            # Act
            response = self.client.delete(f"{self.base_url}/{nonexistent_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_search_vehicles_success(self):
        """Test searching vehicles successfully"""
        # Arrange
        search_results = [self.mock_vehicle]
        search_query = "Toyota"
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.search_vehicles.return_value = search_results
            
            # Act
            response = self.client.get(f"{self.base_url}/search?q={search_query}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["make"] == "Toyota"
            mock_service.search_vehicles.assert_called_once_with(search_query)
    
    @pytest.mark.asyncio
    async def test_get_vehicle_by_registration_success(self):
        """Test getting vehicle by registration number successfully"""
        # Arrange
        registration = "ABC-001"
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicle_by_registration.return_value = self.mock_vehicle
            
            # Act
            response = self.client.get(f"{self.base_url}/registration/{registration}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["registration_number"] == registration
            mock_service.get_vehicle_by_registration.assert_called_once_with(registration)
    
    @pytest.mark.asyncio
    async def test_get_vehicles_by_department_success(self):
        """Test getting vehicles by department successfully"""
        # Arrange
        department = "operations"
        department_vehicles = [self.mock_vehicle]
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicles_by_department.return_value = department_vehicles
            
            # Act
            response = self.client.get(f"{self.base_url}/department/{department}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["department"] == department
            mock_service.get_vehicles_by_department.assert_called_once_with(department)
    
    @pytest.mark.asyncio
    async def test_get_available_vehicles_success(self):
        """Test getting available vehicles successfully"""
        # Arrange
        available_vehicles = [self.mock_vehicle]
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_available_vehicles.return_value = available_vehicles
            
            # Act
            response = self.client.get(f"{self.base_url}/available")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["status"] == "available"
            mock_service.get_available_vehicles.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_vehicle_maintenance_history_success(self):
        """Test getting vehicle maintenance history successfully"""
        # Arrange
        maintenance_history = [
            {
                "id": str(ObjectId()),
                "vehicle_id": self.vehicle_id,
                "maintenance_type": "oil_change",
                "date": datetime.now(timezone.utc),
                "mileage": 15000,
                "cost": 50.0,
                "description": "Regular oil change",
                "performed_by": "Maintenance Team"
            }
        ]
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicle_maintenance_history.return_value = maintenance_history
            
            # Act
            response = self.client.get(f"{self.base_url}/{self.vehicle_id}/maintenance")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["maintenance_type"] == "oil_change"
            mock_service.get_vehicle_maintenance_history.assert_called_once_with(self.vehicle_id)
    
    @pytest.mark.asyncio
    async def test_get_vehicle_assignment_history_success(self):
        """Test getting vehicle assignment history successfully"""
        # Arrange
        assignment_history = [
            {
                "id": str(ObjectId()),
                "vehicle_id": self.vehicle_id,
                "driver_id": str(ObjectId()),
                "driver_name": "John Doe",
                "assignment_type": "regular",
                "start_date": datetime.now(timezone.utc),
                "end_date": None,
                "status": "active"
            }
        ]
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicle_assignment_history.return_value = assignment_history
            
            # Act
            response = self.client.get(f"{self.base_url}/{self.vehicle_id}/assignments")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["assignment_type"] == "regular"
            mock_service.get_vehicle_assignment_history.assert_called_once_with(self.vehicle_id)
    
    @pytest.mark.asyncio
    async def test_bulk_update_vehicles_success(self):
        """Test bulk updating vehicles successfully"""
        # Arrange
        bulk_update_data = {
            "vehicle_ids": [self.vehicle_id, str(ObjectId())],
            "updates": {
                "department": "maintenance",
                "status": "maintenance"
            }
        }
        
        bulk_update_result = {
            "updated_count": 2,
            "successful_updates": [self.vehicle_id, str(ObjectId())],
            "failed_updates": []
        }
        
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.bulk_update_vehicles.return_value = bulk_update_result
            
            # Act
            response = self.client.put(f"{self.base_url}/bulk-update", json=bulk_update_data)
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["updated_count"] == 2
            assert len(data["data"]["successful_updates"]) == 2
            mock_service.bulk_update_vehicles.assert_called_once_with(
                bulk_update_data["vehicle_ids"],
                bulk_update_data["updates"],
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_vehicle_permission_requirements(self):
        """Test that vehicle routes require proper permissions"""
        # Arrange
        unauthorized_user = {
            "user_id": "test_user",
            "role": "guest",
            "permissions": ["analytics:read"],  # No vehicle permissions
            "department": "guest"
        }
        
        with patch('api.routes.vehicles.get_current_user') as mock_auth:
            mock_auth.return_value = unauthorized_user
            
            # Act & Assert - Test various endpoints
            test_cases = [
                ("POST", f"{self.base_url}/", {"registration_number": "TEST-001"}),
                ("GET", f"{self.base_url}/", None),
                ("PUT", f"{self.base_url}/{self.vehicle_id}", {"mileage": 16000}),
                ("DELETE", f"{self.base_url}/{self.vehicle_id}", None)
            ]
            
            for method, url, data in test_cases:
                if method == "POST":
                    response = self.client.post(url, json=data)
                elif method == "PUT":
                    response = self.client.put(url, json=data)
                elif method == "DELETE":
                    response = self.client.delete(url)
                else:
                    response = self.client.get(url)
                
                assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_vehicle_service_error_handling(self):
        """Test error handling when vehicle service raises exceptions"""
        # Arrange
        with patch('api.routes.vehicles.vehicle_service') as mock_service, \
             patch('api.routes.vehicles.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicles.side_effect = Exception("Database connection failed")
            
            # Act
            response = self.client.get(f"{self.base_url}/")
            
            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    @pytest.mark.asyncio
    async def test_vehicle_validation_edge_cases(self):
        """Test vehicle validation edge cases"""
        # Arrange
        edge_case_data = {
            "registration_number": "ABC-001",
            "license_plate": "ABC001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2050,  # Future year
            "color": "White",
            "fuel_type": "petrol",
            "engine_size": 0.1,  # Very small engine
            "mileage": 1000000,  # Very high mileage
            "status": "available",
            "department": "operations",
            "acquisition_date": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.vehicles.get_current_user') as mock_auth:
            mock_auth.return_value = self.mock_user
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=edge_case_data)
            
            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["success"] is False
            assert "validation" in data["error"].lower() or "invalid" in data["error"].lower()
