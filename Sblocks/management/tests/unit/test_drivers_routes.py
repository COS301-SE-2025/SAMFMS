"""
Unit tests for drivers routes
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from api.routes.drivers import router
from schemas.requests import DriverCreateRequest, DriverUpdateRequest
from schemas.responses import StandardResponse

# Create a test app instance
app = FastAPI()
app.include_router(router)


@pytest.mark.unit
@pytest.mark.api
class TestDriversRoutes:
    """Test class for drivers API routes"""
    
    def setup_method(self):
        """Setup test client and dependencies"""
        self.client = TestClient(app)
        self.base_url = "/api/v1/drivers"
        
        # Mock authentication
        self.mock_user = {
            "user_id": "test_user",
            "role": "manager",
            "permissions": ["drivers:read", "drivers:create", "drivers:update"],
            "department": "operations"
        }
        
        # Mock driver data
        self.driver_id = str(ObjectId())
        self.mock_driver = {
            "_id": self.driver_id,
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "phone": "+1234567890",
            "license_number": "DL123456789",
            "license_class": "B",
            "license_expiry": datetime.now(timezone.utc),
            "hire_date": datetime.now(timezone.utc),
            "department": "operations",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
    @pytest.mark.asyncio
    async def test_create_driver_success(self):
        """Test creating driver successfully"""
        # Arrange
        driver_data = {
            "employee_id": "EMP002",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@company.com",
            "phone": "+1234567891",
            "license_number": "DL987654321",
            "license_class": "B",
            "license_expiry": datetime.now(timezone.utc).isoformat(),
            "hire_date": datetime.now(timezone.utc).isoformat(),
            "department": "operations"
        }
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.create_driver.return_value = self.mock_driver
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=driver_data)
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["success"] is True
            assert data["data"]["employee_id"] == "EMP001"  # From mock
            assert data["data"]["first_name"] == "John"
            mock_service.create_driver.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_driver_invalid_data(self):
        """Test creating driver with invalid data"""
        # Arrange
        invalid_data = {
            "employee_id": "",  # Empty employee ID
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "invalid_email",  # Invalid email format
            "phone": "123",  # Invalid phone format
            "license_number": "",  # Empty license number
            "license_class": "X",  # Invalid license class
            "license_expiry": "invalid_date",  # Invalid date format
            "hire_date": "invalid_date",  # Invalid date format
            "department": ""  # Empty department
        }
        
        with patch('api.routes.drivers.get_current_user') as mock_auth:
            mock_auth.return_value = self.mock_user
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=invalid_data)
            
            # Assert
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_get_driver_success(self):
        """Test getting driver by ID successfully"""
        # Arrange
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_driver_by_id.return_value = self.mock_driver
            
            # Act
            response = self.client.get(f"{self.base_url}/{self.driver_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["_id"] == self.driver_id
            assert data["data"]["first_name"] == "John"
            mock_service.get_driver_by_id.assert_called_once_with(self.driver_id)
    
    @pytest.mark.asyncio
    async def test_get_driver_not_found(self):
        """Test getting driver that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_driver_by_id.return_value = None
            
            # Act
            response = self.client.get(f"{self.base_url}/{nonexistent_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_get_drivers_list_success(self):
        """Test getting drivers list successfully"""
        # Arrange
        mock_drivers = [
            self.mock_driver,
            {
                "_id": str(ObjectId()),
                "employee_id": "EMP003",
                "first_name": "Mike",
                "last_name": "Johnson",
                "email": "mike.johnson@company.com",
                "phone": "+1234567892",
                "license_number": "DL555666777",
                "license_class": "C",
                "department": "maintenance",
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_drivers.return_value = mock_drivers
            
            # Act
            response = self.client.get(f"{self.base_url}/")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["data"][0]["employee_id"] == "EMP001"
            assert data["data"][1]["employee_id"] == "EMP003"
            mock_service.get_drivers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_drivers_with_filters(self):
        """Test getting drivers list with filters"""
        # Arrange
        filtered_drivers = [self.mock_driver]
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_drivers.return_value = filtered_drivers
            
            # Act
            response = self.client.get(f"{self.base_url}/?status=active&department=operations")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["status"] == "active"
            assert data["data"][0]["department"] == "operations"
            mock_service.get_drivers.assert_called_once_with(
                status="active",
                department="operations"
            )
    
    @pytest.mark.asyncio
    async def test_get_drivers_with_pagination(self):
        """Test getting drivers list with pagination"""
        # Arrange
        mock_drivers = [self.mock_driver]
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_drivers.return_value = mock_drivers
            
            # Act
            response = self.client.get(f"{self.base_url}/?page=1&page_size=10")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            mock_service.get_drivers.assert_called_once_with(
                page=1,
                page_size=10
            )
    
    @pytest.mark.asyncio
    async def test_update_driver_success(self):
        """Test updating driver successfully"""
        # Arrange
        update_data = {
            "phone": "+1234567999",
            "department": "maintenance",
            "status": "inactive"
        }
        
        updated_driver = {
            **self.mock_driver,
            **update_data,
            "updated_at": datetime.now(timezone.utc)
        }
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.update_driver.return_value = updated_driver
            
            # Act
            response = self.client.put(f"{self.base_url}/{self.driver_id}", json=update_data)
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["phone"] == "+1234567999"
            assert data["data"]["department"] == "maintenance"
            mock_service.update_driver.assert_called_once_with(
                self.driver_id,
                update_data,
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_update_driver_not_found(self):
        """Test updating driver that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        update_data = {"phone": "+1234567999"}
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.update_driver.return_value = None
            
            # Act
            response = self.client.put(f"{self.base_url}/{nonexistent_id}", json=update_data)
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_driver_success(self):
        """Test deleting driver successfully"""
        # Arrange
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.delete_driver.return_value = True
            
            # Act
            response = self.client.delete(f"{self.base_url}/{self.driver_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "deleted" in data["message"].lower()
            mock_service.delete_driver.assert_called_once_with(
                self.driver_id,
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_delete_driver_not_found(self):
        """Test deleting driver that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.delete_driver.return_value = False
            
            # Act
            response = self.client.delete(f"{self.base_url}/{nonexistent_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_search_drivers_success(self):
        """Test searching drivers successfully"""
        # Arrange
        search_results = [self.mock_driver]
        search_query = "John"
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.search_drivers.return_value = search_results
            
            # Act
            response = self.client.get(f"{self.base_url}/search?q={search_query}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["first_name"] == "John"
            mock_service.search_drivers.assert_called_once_with(search_query)
    
    @pytest.mark.asyncio
    async def test_get_driver_by_employee_id_success(self):
        """Test getting driver by employee ID successfully"""
        # Arrange
        employee_id = "EMP001"
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_driver_by_employee_id.return_value = self.mock_driver
            
            # Act
            response = self.client.get(f"{self.base_url}/employee/{employee_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["employee_id"] == employee_id
            mock_service.get_driver_by_employee_id.assert_called_once_with(employee_id)
    
    @pytest.mark.asyncio
    async def test_get_drivers_by_department_success(self):
        """Test getting drivers by department successfully"""
        # Arrange
        department = "operations"
        department_drivers = [self.mock_driver]
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_drivers_by_department.return_value = department_drivers
            
            # Act
            response = self.client.get(f"{self.base_url}/department/{department}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["department"] == department
            mock_service.get_drivers_by_department.assert_called_once_with(department)
    
    @pytest.mark.asyncio
    async def test_get_available_drivers_success(self):
        """Test getting available drivers successfully"""
        # Arrange
        available_drivers = [self.mock_driver]
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_available_drivers.return_value = available_drivers
            
            # Act
            response = self.client.get(f"{self.base_url}/available")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["status"] == "active"
            mock_service.get_available_drivers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_vehicle_to_driver_success(self):
        """Test assigning vehicle to driver successfully"""
        # Arrange
        vehicle_id = str(ObjectId())
        assignment_data = {
            "vehicle_id": vehicle_id,
            "assignment_type": "regular",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "notes": "Regular assignment"
        }
        
        mock_assignment = {
            "_id": str(ObjectId()),
            "driver_id": self.driver_id,
            "vehicle_id": vehicle_id,
            "assignment_type": "regular",
            "status": "active",
            "start_date": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc)
        }
        
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.assign_vehicle_to_driver.return_value = mock_assignment
            
            # Act
            response = self.client.post(
                f"{self.base_url}/{self.driver_id}/assign-vehicle",
                json=assignment_data
            )
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["success"] is True
            assert data["data"]["driver_id"] == self.driver_id
            assert data["data"]["vehicle_id"] == vehicle_id
            mock_service.assign_vehicle_to_driver.assert_called_once_with(
                self.driver_id,
                vehicle_id,
                assignment_data,
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_driver_permission_requirements(self):
        """Test that driver routes require proper permissions"""
        # Arrange
        unauthorized_user = {
            "user_id": "test_user",
            "role": "guest",
            "permissions": ["analytics:read"],  # No driver permissions
            "department": "guest"
        }
        
        with patch('api.routes.drivers.get_current_user') as mock_auth:
            mock_auth.return_value = unauthorized_user
            
            # Act & Assert - Test various endpoints
            test_cases = [
                ("POST", f"{self.base_url}/", {"employee_id": "EMP001"}),
                ("GET", f"{self.base_url}/", None),
                ("PUT", f"{self.base_url}/{self.driver_id}", {"phone": "+1234567890"}),
                ("DELETE", f"{self.base_url}/{self.driver_id}", None)
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
    async def test_driver_service_error_handling(self):
        """Test error handling when driver service raises exceptions"""
        # Arrange
        with patch('api.routes.drivers.driver_service') as mock_service, \
             patch('api.routes.drivers.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_drivers.side_effect = Exception("Database connection failed")
            
            # Act
            response = self.client.get(f"{self.base_url}/")
            
            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    @pytest.mark.asyncio
    async def test_driver_validation_edge_cases(self):
        """Test driver validation edge cases"""
        # Arrange
        edge_case_data = {
            "employee_id": "EMP001",
            "first_name": "J",  # Too short
            "last_name": "D",   # Too short
            "email": "valid@email.com",
            "phone": "+1234567890",
            "license_number": "DL123456789",
            "license_class": "B",
            "license_expiry": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),  # Expired
            "hire_date": datetime.now(timezone.utc).isoformat(),
            "department": "operations"
        }
        
        with patch('api.routes.drivers.get_current_user') as mock_auth:
            mock_auth.return_value = self.mock_user
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=edge_case_data)
            
            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["success"] is False
            assert "validation" in data["error"].lower() or "expired" in data["error"].lower()
