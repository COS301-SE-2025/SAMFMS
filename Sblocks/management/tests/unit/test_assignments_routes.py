"""
Unit tests for assignments routes
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from api.routes.assignments import router
from schemas.requests import AssignmentCreateRequest, AssignmentUpdateRequest
from schemas.responses import StandardResponse

# Create a test app instance
app = FastAPI()
app.include_router(router)


@pytest.mark.unit
@pytest.mark.api
class TestAssignmentsRoutes:
    """Test class for assignments API routes"""
    
    def setup_method(self):
        """Setup test client and dependencies"""
        self.client = TestClient(app)
        self.base_url = "/api/v1/assignments"
        
        # Mock authentication
        self.mock_user = {
            "user_id": "test_user",
            "role": "manager",
            "permissions": ["assignments:read", "assignments:create", "assignments:update"],
            "department": "operations"
        }
        
        # Mock assignment data
        self.assignment_id = str(ObjectId())
        self.mock_assignment = {
            "_id": self.assignment_id,
            "vehicle_id": str(ObjectId()),
            "driver_id": str(ObjectId()),
            "assignment_type": "regular",
            "status": "active",
            "start_date": datetime.now(timezone.utc),
            "end_date": None,
            "notes": "Test assignment",
            "created_by": "test_user",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
    @pytest.mark.asyncio
    async def test_create_assignment_success(self):
        """Test creating assignment successfully"""
        # Arrange
        assignment_data = {
            "vehicle_id": str(ObjectId()),
            "driver_id": str(ObjectId()),
            "assignment_type": "regular",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "notes": "Test assignment creation"
        }
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.create_assignment.return_value = self.mock_assignment
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=assignment_data)
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["success"] is True
            assert data["data"]["vehicle_id"] == assignment_data["vehicle_id"]
            assert data["data"]["driver_id"] == assignment_data["driver_id"]
            mock_service.create_assignment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_assignment_invalid_data(self):
        """Test creating assignment with invalid data"""
        # Arrange
        invalid_data = {
            "vehicle_id": "invalid_id",  # Invalid ObjectId
            "driver_id": str(ObjectId()),
            "assignment_type": "invalid_type",  # Invalid type
            "start_date": "invalid_date"  # Invalid date format
        }
        
        with patch('api.routes.assignments.get_current_user') as mock_auth:
            mock_auth.return_value = self.mock_user
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=invalid_data)
            
            # Assert
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_get_assignment_success(self):
        """Test getting assignment by ID successfully"""
        # Arrange
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignment_by_id.return_value = self.mock_assignment
            
            # Act
            response = self.client.get(f"{self.base_url}/{self.assignment_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["_id"] == self.assignment_id
            mock_service.get_assignment_by_id.assert_called_once_with(self.assignment_id)
    
    @pytest.mark.asyncio
    async def test_get_assignment_not_found(self):
        """Test getting assignment that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignment_by_id.return_value = None
            
            # Act
            response = self.client.get(f"{self.base_url}/{nonexistent_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_get_assignments_list_success(self):
        """Test getting assignments list successfully"""
        # Arrange
        mock_assignments = [
            self.mock_assignment,
            {
                "_id": str(ObjectId()),
                "vehicle_id": str(ObjectId()),
                "driver_id": str(ObjectId()),
                "assignment_type": "temporary",
                "status": "completed",
                "start_date": datetime.now(timezone.utc),
                "end_date": datetime.now(timezone.utc),
                "created_by": "test_user",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignments.return_value = mock_assignments
            
            # Act
            response = self.client.get(f"{self.base_url}/")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["data"][0]["assignment_type"] == "regular"
            assert data["data"][1]["assignment_type"] == "temporary"
            mock_service.get_assignments.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_assignments_with_filters(self):
        """Test getting assignments list with filters"""
        # Arrange
        filtered_assignments = [self.mock_assignment]
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignments.return_value = filtered_assignments
            
            # Act
            response = self.client.get(f"{self.base_url}/?status=active&assignment_type=regular")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["status"] == "active"
            mock_service.get_assignments.assert_called_once_with(
                status="active",
                assignment_type="regular"
            )
    
    @pytest.mark.asyncio
    async def test_get_assignments_with_pagination(self):
        """Test getting assignments list with pagination"""
        # Arrange
        mock_assignments = [self.mock_assignment]
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignments.return_value = mock_assignments
            
            # Act
            response = self.client.get(f"{self.base_url}/?page=1&page_size=10")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            mock_service.get_assignments.assert_called_once_with(
                page=1,
                page_size=10
            )
    
    @pytest.mark.asyncio
    async def test_update_assignment_success(self):
        """Test updating assignment successfully"""
        # Arrange
        update_data = {
            "status": "completed",
            "end_date": datetime.now(timezone.utc).isoformat(),
            "notes": "Updated assignment notes"
        }
        
        updated_assignment = {
            **self.mock_assignment,
            **update_data,
            "updated_at": datetime.now(timezone.utc)
        }
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.update_assignment.return_value = updated_assignment
            
            # Act
            response = self.client.put(f"{self.base_url}/{self.assignment_id}", json=update_data)
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "completed"
            assert data["data"]["notes"] == "Updated assignment notes"
            mock_service.update_assignment.assert_called_once_with(
                self.assignment_id,
                update_data,
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_update_assignment_not_found(self):
        """Test updating assignment that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        update_data = {"status": "completed"}
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.update_assignment.return_value = None
            
            # Act
            response = self.client.put(f"{self.base_url}/{nonexistent_id}", json=update_data)
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_assignment_success(self):
        """Test deleting assignment successfully"""
        # Arrange
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.delete_assignment.return_value = True
            
            # Act
            response = self.client.delete(f"{self.base_url}/{self.assignment_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "deleted" in data["message"].lower()
            mock_service.delete_assignment.assert_called_once_with(
                self.assignment_id,
                "test_user"
            )
    
    @pytest.mark.asyncio
    async def test_delete_assignment_not_found(self):
        """Test deleting assignment that doesn't exist"""
        # Arrange
        nonexistent_id = str(ObjectId())
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.delete_assignment.return_value = False
            
            # Act
            response = self.client.delete(f"{self.base_url}/{nonexistent_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["success"] is False
            assert "not found" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_get_active_assignments_success(self):
        """Test getting active assignments successfully"""
        # Arrange
        active_assignments = [self.mock_assignment]
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_active_assignments.return_value = active_assignments
            
            # Act
            response = self.client.get(f"{self.base_url}/active")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            assert data["data"][0]["status"] == "active"
            mock_service.get_active_assignments.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_assignments_by_driver_success(self):
        """Test getting assignments by driver successfully"""
        # Arrange
        driver_id = str(ObjectId())
        driver_assignments = [self.mock_assignment]
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignments_by_driver.return_value = driver_assignments
            
            # Act
            response = self.client.get(f"{self.base_url}/driver/{driver_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            mock_service.get_assignments_by_driver.assert_called_once_with(driver_id)
    
    @pytest.mark.asyncio
    async def test_get_assignments_by_vehicle_success(self):
        """Test getting assignments by vehicle successfully"""
        # Arrange
        vehicle_id = str(ObjectId())
        vehicle_assignments = [self.mock_assignment]
        
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignments_by_vehicle.return_value = vehicle_assignments
            
            # Act
            response = self.client.get(f"{self.base_url}/vehicle/{vehicle_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            mock_service.get_assignments_by_vehicle.assert_called_once_with(vehicle_id)
    
    @pytest.mark.asyncio
    async def test_assignment_permission_requirements(self):
        """Test that assignment routes require proper permissions"""
        # Arrange
        unauthorized_user = {
            "user_id": "test_user",
            "role": "driver",
            "permissions": ["drivers:read"],  # No assignment permissions
            "department": "operations"
        }
        
        with patch('api.routes.assignments.get_current_user') as mock_auth:
            mock_auth.return_value = unauthorized_user
            
            # Act & Assert - Test various endpoints
            test_cases = [
                ("POST", f"{self.base_url}/", {"vehicle_id": str(ObjectId())}),
                ("GET", f"{self.base_url}/", None),
                ("PUT", f"{self.base_url}/{self.assignment_id}", {"status": "completed"}),
                ("DELETE", f"{self.base_url}/{self.assignment_id}", None)
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
    async def test_assignment_service_error_handling(self):
        """Test error handling when assignment service raises exceptions"""
        # Arrange
        with patch('api.routes.assignments.assignment_service') as mock_service, \
             patch('api.routes.assignments.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignments.side_effect = Exception("Database connection failed")
            
            # Act
            response = self.client.get(f"{self.base_url}/")
            
            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    @pytest.mark.asyncio
    async def test_assignment_validation_edge_cases(self):
        """Test assignment validation edge cases"""
        # Arrange
        edge_case_data = {
            "vehicle_id": str(ObjectId()),
            "driver_id": str(ObjectId()),
            "assignment_type": "regular",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "end_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()  # End before start
        }
        
        with patch('api.routes.assignments.get_current_user') as mock_auth:
            mock_auth.return_value = self.mock_user
            
            # Act
            response = self.client.post(f"{self.base_url}/", json=edge_case_data)
            
            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["success"] is False
            assert "end_date" in data["error"].lower() or "start_date" in data["error"].lower()
