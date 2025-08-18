"""
Unit tests for driver service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from services.driver_service import DriverService
from schemas.requests import DriverCreateRequest, DriverUpdateRequest
from schemas.entities import Driver


@pytest.mark.unit
@pytest.mark.driver
class TestDriverService:
    """Test class for DriverService"""
    
    @pytest.fixture
    def driver_service(self, mock_mongodb):
        """Create DriverService instance for testing"""
        return DriverService()
    
    @pytest.fixture
    def sample_driver_data(self):
        """Sample driver data for testing"""
        return {
            "_id": ObjectId(),
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "phone": "+27123456789",
            "license_number": "1234567890",
            "license_class": ["B", "EB"],
            "license_expiry": datetime(2025, 12, 31),
            "status": "active",
            "department": "Security",
            "hire_date": datetime(2020, 1, 15),
            "current_vehicle_id": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    
    @pytest.fixture
    def sample_driver_create_request(self):
        """Sample driver creation request"""
        return DriverCreateRequest(
            employee_id="EMP001",
            first_name="John",
            last_name="Doe",
            email="john.doe@company.com",
            phone="+27123456789",
            license_number="1234567890",
            license_class=["B", "EB"],
            license_expiry=datetime(2025, 12, 31),
            department="Security",
            hire_date=datetime(2020, 1, 15)
        )
       
    # Removed tests for non-existent methods get_driver_by_id and get_drivers
    
    @pytest.mark.asyncio
    async def test_update_driver_success(self, driver_service, sample_driver_data):
        """Test successful driver update"""
        # Arrange
        driver_id = str(sample_driver_data["_id"])
        update_data = DriverUpdateRequest(
            first_name="Jane",
            last_name="Smith",
            phone="+27987654321"
        )
        updated_by = "test_user"
        
        updated_driver = sample_driver_data.copy()
        updated_driver["first_name"] = "Jane"
        updated_driver["last_name"] = "Smith"
        updated_driver["phone"] = "+27987654321"
        
        with patch.object(driver_service.driver_repo, 'get_by_id', return_value=sample_driver_data), \
             patch.object(driver_service.driver_repo, 'update', return_value=True), \
             patch.object(driver_service.driver_repo, 'get_by_id', return_value=updated_driver):
            
            # Act
            result = await driver_service.update_driver(driver_id, update_data, updated_by)
            
            # Assert
            assert result is not None
            assert result["first_name"] == "Jane"
            assert result["last_name"] == "Smith"
            assert result["phone"] == "+27987654321"
    
    @pytest.mark.asyncio
    async def test_update_driver_not_found(self, driver_service):
        """Test driver update with non-existent ID"""
        # Arrange
        driver_id = str(ObjectId())
        update_data = DriverUpdateRequest(first_name="Jane")
        updated_by = "test_user"
        
        with patch.object(driver_service.driver_repo, 'get_by_id', return_value=None):
            
            # Act & Assert
            with pytest.raises(ValueError, match="not found"):
                await driver_service.update_driver(driver_id, update_data, updated_by)
    
    # Removed tests for non-existent methods delete_driver and assignment_repo
    
    @pytest.mark.asyncio
    async def test_get_drivers_by_department(self, driver_service, sample_driver_data):
        """Test getting drivers by department"""
        # Arrange
        department = "Security"
        drivers = [sample_driver_data]
        
        with patch.object(driver_service.driver_repo, 'get_by_department', return_value=drivers):
            
            # Act
            result = await driver_service.get_drivers_by_department(department)
            
            # Assert
            assert result is not None
            assert len(result) == 1
            assert result[0]["department"] == "Security"
    
    @pytest.mark.asyncio
    async def test_search_drivers(self, driver_service, sample_driver_data):
        """Test driver search functionality"""
        # Arrange
        query = "John"
        drivers = [sample_driver_data]
        
        with patch.object(driver_service.driver_repo, 'search_drivers', return_value=drivers):
            
            # Act
            result = await driver_service.search_drivers(query)
            
            # Assert
            assert result is not None
            assert len(result) == 1
            assert result[0]["first_name"] == "John"
