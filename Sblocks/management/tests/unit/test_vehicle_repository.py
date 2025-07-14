"""
Unit tests for VehicleRepository
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime

from repositories.repositories import VehicleRepository
from tests.conftest import create_mock_cursor


@pytest.mark.unit
@pytest.mark.vehicle
class TestVehicleRepository:
    """Test cases for VehicleRepository"""

    @pytest.fixture
    def vehicle_repo(self, mock_mongodb):
        """Create VehicleRepository instance with mocked database"""
        return VehicleRepository()

    @pytest.mark.asyncio
    async def test_create_vehicle(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test vehicle creation in repository"""
        # Arrange
        vehicle_data = sample_vehicle_data.copy()
        vehicle_data.pop("_id")  # Remove _id for creation
        expected_id = str(ObjectId())
        
        mock_mongodb.vehicles.insert_one.return_value.inserted_id = expected_id

        # Act
        result = await vehicle_repo.create(vehicle_data)

        # Assert
        assert result == expected_id
        mock_mongodb.vehicles.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test getting vehicle by ID when found"""
        # Arrange
        vehicle_id = str(sample_vehicle_data["_id"])
        mock_mongodb.vehicles.find_one.return_value = sample_vehicle_data

        # Act
        result = await vehicle_repo.get_by_id(vehicle_id)

        # Assert
        assert result == sample_vehicle_data
        mock_mongodb.vehicles.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, vehicle_repo, mock_mongodb):
        """Test getting vehicle by ID when not found"""
        # Arrange
        vehicle_id = str(ObjectId())
        mock_mongodb.vehicles.find_one.return_value = None

        # Act
        result = await vehicle_repo.get_by_id(vehicle_id)

        # Assert
        assert result is None
        mock_mongodb.vehicles.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_registration_number(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test getting vehicle by registration number"""
        # Arrange
        registration_number = sample_vehicle_data["registration_number"]
        mock_mongodb.vehicles.find_one.return_value = sample_vehicle_data

        # Act
        result = await vehicle_repo.get_by_registration_number(registration_number)

        # Assert
        assert result == sample_vehicle_data
        mock_mongodb.vehicles.find_one.assert_called_once_with(
            {"registration_number": registration_number}
        )

    @pytest.mark.asyncio
    async def test_get_all_vehicles(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test getting all vehicles"""
        # Arrange
        vehicles = [sample_vehicle_data]
        mock_cursor = create_mock_cursor(vehicles)
        mock_mongodb.vehicles.find.return_value = mock_cursor

        # Act
        result = await vehicle_repo.get_all()

        # Assert
        assert result == vehicles
        mock_mongodb.vehicles.find.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_get_all_with_filter(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test getting vehicles with filter"""
        # Arrange
        vehicles = [sample_vehicle_data]
        filter_query = {"department": "Security"}
        mock_cursor = create_mock_cursor(vehicles)
        mock_mongodb.vehicles.find.return_value = mock_cursor

        # Act
        result = await vehicle_repo.get_all(filter_query)

        # Assert
        assert result == vehicles
        mock_mongodb.vehicles.find.assert_called_once_with(filter_query)

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test getting vehicles with pagination"""
        # Arrange
        vehicles = [sample_vehicle_data]
        skip = 10
        limit = 5
        mock_cursor = create_mock_cursor(vehicles)
        mock_mongodb.vehicles.find.return_value = mock_cursor

        # Act
        result = await vehicle_repo.get_all({}, skip=skip, limit=limit)

        # Assert
        assert result == vehicles
        mock_cursor.skip.assert_called_once_with(skip)
        mock_cursor.limit.assert_called_once_with(limit)

    @pytest.mark.asyncio
    async def test_update_vehicle(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test updating vehicle"""
        # Arrange
        vehicle_id = str(sample_vehicle_data["_id"])
        update_data = {"status": "maintenance", "mileage": 20000}
        mock_mongodb.vehicles.update_one.return_value.matched_count = 1

        # Act
        result = await vehicle_repo.update(vehicle_id, update_data)

        # Assert
        assert result is True
        mock_mongodb.vehicles.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self, vehicle_repo, mock_mongodb):
        """Test updating non-existent vehicle"""
        # Arrange
        vehicle_id = str(ObjectId())
        update_data = {"status": "maintenance"}
        mock_mongodb.vehicles.update_one.return_value.matched_count = 0

        # Act
        result = await vehicle_repo.update(vehicle_id, update_data)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_vehicle(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test deleting vehicle"""
        # Arrange
        vehicle_id = str(sample_vehicle_data["_id"])
        mock_mongodb.vehicles.delete_one.return_value.deleted_count = 1

        # Act
        result = await vehicle_repo.delete(vehicle_id)

        # Assert
        assert result is True
        mock_mongodb.vehicles.delete_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_vehicle_not_found(self, vehicle_repo, mock_mongodb):
        """Test deleting non-existent vehicle"""
        # Arrange
        vehicle_id = str(ObjectId())
        mock_mongodb.vehicles.delete_one.return_value.deleted_count = 0

        # Act
        result = await vehicle_repo.delete(vehicle_id)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_count_vehicles(self, vehicle_repo, mock_mongodb):
        """Test counting vehicles"""
        # Arrange
        expected_count = 5
        mock_mongodb.vehicles.count_documents.return_value = expected_count

        # Act
        result = await vehicle_repo.count()

        # Assert
        assert result == expected_count
        mock_mongodb.vehicles.count_documents.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_count_vehicles_with_filter(self, vehicle_repo, mock_mongodb):
        """Test counting vehicles with filter"""
        # Arrange
        filter_query = {"status": "available"}
        expected_count = 3
        mock_mongodb.vehicles.count_documents.return_value = expected_count

        # Act
        result = await vehicle_repo.count(filter_query)

        # Assert
        assert result == expected_count
        mock_mongodb.vehicles.count_documents.assert_called_once_with(filter_query)

    @pytest.mark.asyncio
    async def test_search_vehicles(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test searching vehicles"""
        # Arrange
        search_term = "Toyota"
        vehicles = [sample_vehicle_data]
        mock_cursor = create_mock_cursor(vehicles)
        mock_mongodb.vehicles.find.return_value = mock_cursor

        # Act
        result = await vehicle_repo.search(search_term)

        # Assert
        assert result == vehicles
        # Verify that find was called with a regex search query
        call_args = mock_mongodb.vehicles.find.call_args[0][0]
        assert "$or" in call_args
        mock_mongodb.vehicles.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_department(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test getting vehicles by department"""
        # Arrange
        department = "Security"
        vehicles = [sample_vehicle_data]
        mock_cursor = create_mock_cursor(vehicles)
        mock_mongodb.vehicles.find.return_value = mock_cursor

        # Act
        result = await vehicle_repo.get_by_department(department)

        # Assert
        assert result == vehicles
        mock_mongodb.vehicles.find.assert_called_once_with({"department": department})

    @pytest.mark.asyncio
    async def test_get_available_vehicles(self, vehicle_repo, sample_vehicle_data, mock_mongodb):
        """Test getting available vehicles"""
        # Arrange
        vehicles = [sample_vehicle_data]
        mock_cursor = create_mock_cursor(vehicles)
        mock_mongodb.vehicles.find.return_value = mock_cursor

        # Act
        result = await vehicle_repo.get_available_vehicles()

        # Assert
        assert result == vehicles
        mock_mongodb.vehicles.find.assert_called_once_with({"status": "available"})
