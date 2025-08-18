"""
Unit tests for driver repository
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from repositories.repositories import DriverRepository
from tests.conftest import create_mock_cursor


@pytest.mark.unit
@pytest.mark.driver
class TestDriverRepository:
    """Test class for DriverRepository"""
    
    @pytest.fixture
    def driver_repo(self, mock_mongodb):
        """Create DriverRepository instance for testing"""
        return DriverRepository()
    
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
    
    @pytest.mark.asyncio
    async def test_create_driver(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test creating a driver"""
        # Arrange
        mock_mongodb.drivers.insert_one.return_value.inserted_id = sample_driver_data["_id"]
        
        # Act
        result = await driver_repo.create(sample_driver_data)
        
        # Assert
        assert result is not None
        assert result == str(sample_driver_data["_id"])  # create method returns string ID
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test getting driver by ID when found"""
        # Arrange
        driver_id = str(sample_driver_data["_id"])
        mock_mongodb.drivers.find_one.return_value = sample_driver_data
        
        # Act
        result = await driver_repo.get_by_id(driver_id)
        
        # Assert
        assert result is not None
        assert result["_id"] == sample_driver_data["_id"]
        assert result["employee_id"] == "EMP001"
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, driver_repo, mock_mongodb):
        """Test getting driver by ID when not found"""
        # Arrange
        driver_id = str(ObjectId())
        mock_mongodb.drivers.find_one.return_value = None
        
        # Act
        result = await driver_repo.get_by_id(driver_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_employee_id(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test getting driver by employee ID"""
        # Arrange
        employee_id = "EMP001"
        mock_mongodb.drivers.find_one.return_value = sample_driver_data
        
        # Act
        result = await driver_repo.get_by_employee_id(employee_id)
        
        # Assert
        assert result is not None
        assert result["employee_id"] == employee_id
    
    @pytest.mark.asyncio
    async def test_get_all_drivers(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test getting all drivers"""
        # Arrange
        drivers = [sample_driver_data]
        mock_cursor = create_mock_cursor(drivers)
        mock_mongodb.drivers.find.return_value = mock_cursor
        
        # Act
        result = await driver_repo.find()
        
        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0]["employee_id"] == "EMP001"
    
    @pytest.mark.asyncio
    async def test_get_all_with_filter(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test getting drivers with filter"""
        # Arrange
        drivers = [sample_driver_data]
        mock_cursor = create_mock_cursor(drivers)
        mock_mongodb.drivers.find.return_value = mock_cursor
        filter_query = {"department": "Security"}
        
        # Act
        result = await driver_repo.find(filter_query)
        
        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0]["department"] == "Security"
    
    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test getting drivers with pagination"""
        # Arrange
        drivers = [sample_driver_data]
        mock_cursor = create_mock_cursor(drivers)
        mock_mongodb.drivers.find.return_value = mock_cursor
        skip = 0
        limit = 10
        
        # Act
        result = await driver_repo.find({}, skip=skip, limit=limit)
        
        # Assert
        assert result is not None
        assert len(result) == 1
        mock_cursor.skip.assert_called_once_with(skip)
        mock_cursor.limit.assert_called_once_with(limit)
    
    @pytest.mark.asyncio
    async def test_update_driver(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test updating a driver"""
        # Arrange
        driver_id = str(sample_driver_data["_id"])
        update_data = {"first_name": "Jane", "last_name": "Smith"}
        mock_mongodb.drivers.update_one.return_value.modified_count = 1
        
        # Act
        result = await driver_repo.update(driver_id, update_data)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_driver_not_found(self, driver_repo, mock_mongodb):
        """Test updating non-existent driver"""
        # Arrange
        driver_id = str(ObjectId())
        update_data = {"first_name": "Jane"}
        mock_mongodb.drivers.update_one.return_value.modified_count = 0
        
        # Act
        result = await driver_repo.update(driver_id, update_data)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_driver(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test deleting a driver"""
        # Arrange
        driver_id = str(sample_driver_data["_id"])
        mock_mongodb.drivers.delete_one.return_value.deleted_count = 1
        
        # Act
        result = await driver_repo.delete(driver_id)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_driver_not_found(self, driver_repo, mock_mongodb):
        """Test deleting non-existent driver"""
        # Arrange
        driver_id = str(ObjectId())
        mock_mongodb.drivers.delete_one.return_value.deleted_count = 0
        
        # Act
        result = await driver_repo.delete(driver_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_count_drivers(self, driver_repo, mock_mongodb):
        """Test counting drivers"""
        # Arrange
        mock_mongodb.drivers.count_documents.return_value = 5
        
        # Act
        result = await driver_repo.count()
        
        # Assert
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_count_drivers_with_filter(self, driver_repo, mock_mongodb):
        """Test counting drivers with filter"""
        # Arrange
        mock_mongodb.drivers.count_documents.return_value = 2
        filter_query = {"department": "Security"}
        
        # Act
        result = await driver_repo.count(filter_query)
        
        # Assert
        assert result == 2
    
    @pytest.mark.asyncio
    async def test_search_drivers(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test searching drivers"""
        # Arrange
        drivers = [sample_driver_data]
        mock_cursor = create_mock_cursor(drivers)
        mock_mongodb.drivers.find.return_value = mock_cursor
        query = "John"
        
        # Act
        search_filter = {
            "$or": [
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}},
                {"employee_id": {"$regex": query, "$options": "i"}}
            ]
        }
        result = await driver_repo.find(search_filter)
        
        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0]["first_name"] == "John"
    
    @pytest.mark.asyncio
    async def test_get_by_department(self, driver_repo, sample_driver_data, mock_mongodb):
        """Test getting drivers by department"""
        # Arrange
        drivers = [sample_driver_data]
        mock_cursor = create_mock_cursor(drivers)
        mock_mongodb.drivers.find.return_value = mock_cursor
        department = "Security"
        
        # Act
        result = await driver_repo.get_by_department(department)
        
        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0]["department"] == "Security"
    
    # Removed test for non-existent method get_available_drivers
