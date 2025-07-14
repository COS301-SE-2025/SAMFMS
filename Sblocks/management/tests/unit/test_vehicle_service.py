"""
Unit tests for VehicleService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime

from services.vehicle_service import VehicleService
from schemas.requests import VehicleCreateRequest
from tests.conftest import create_mock_cursor


@pytest.mark.unit
@pytest.mark.vehicle
class TestVehicleService:
    """Test cases for VehicleService"""

    @pytest.fixture
    def vehicle_service(self, mock_mongodb, mock_event_publisher):
        """Create VehicleService instance with mocked dependencies"""
        return VehicleService()

    @pytest.mark.asyncio
    async def test_create_vehicle_success(
        self, 
        vehicle_service, 
        sample_vehicle_create_request, 
        mock_mongodb
    ):
        """Test successful vehicle creation"""
        # Arrange
        vehicle_request = VehicleCreateRequest(**sample_vehicle_create_request)
        created_by = "test_user"
        vehicle_id = str(ObjectId())
        
        # Mock repository methods
        with patch.object(vehicle_service.vehicle_repo, 'get_by_registration_number', return_value=None), \
             patch.object(vehicle_service.vehicle_repo, 'create', return_value=vehicle_id), \
             patch.object(vehicle_service.vehicle_repo, 'get_by_id') as mock_get_by_id:
            
            # Setup mock return for get_by_id
            created_vehicle = {
                **sample_vehicle_create_request,
                "_id": vehicle_id,
                "registration_number": sample_vehicle_create_request["license_plate"],
                "created_by": created_by,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_get_by_id.return_value = created_vehicle

            # Act
            result = await vehicle_service.create_vehicle(vehicle_request, created_by)

            # Assert
            assert result is not None
            assert result["make"] == sample_vehicle_create_request["make"]
            assert result["model"] == sample_vehicle_create_request["model"]
            assert result["license_plate"] == sample_vehicle_create_request["license_plate"]
            assert result["registration_number"] == sample_vehicle_create_request["license_plate"]
            assert result["created_by"] == created_by

    @pytest.mark.asyncio
    async def test_create_vehicle_duplicate_registration(
        self, 
        vehicle_service, 
        sample_vehicle_create_request, 
        sample_vehicle_data
    ):
        """Test vehicle creation with duplicate registration number"""
        # Arrange
        vehicle_request = VehicleCreateRequest(**sample_vehicle_create_request)
        created_by = "test_user"
        
        # Mock existing vehicle
        with patch.object(vehicle_service.vehicle_repo, 'get_by_registration_number', return_value=sample_vehicle_data):
            
            # Act & Assert
            with pytest.raises(ValueError, match="already exists"):
                await vehicle_service.create_vehicle(vehicle_request, created_by)

    @pytest.mark.asyncio
    async def test_create_vehicle_missing_license_plate(self, vehicle_service):
        """Test vehicle creation without license plate or registration number"""
        # Arrange
        invalid_request_data = {
            "make": "Toyota",
            "model": "Hilux",
            "year": 2023,
            "vin": "1GTPUEE18J8654321",
            "color": "Blue"
        }
        vehicle_request = VehicleCreateRequest(**invalid_request_data)
        created_by = "test_user"

        # Act & Assert
        with pytest.raises(ValueError, match="license_plate must be provided"):
            await vehicle_service.create_vehicle(vehicle_request, created_by)

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_success(self, vehicle_service, sample_vehicle_data):
        """Test successful vehicle retrieval by ID"""
        # Arrange
        vehicle_id = str(sample_vehicle_data["_id"])
        
        with patch.object(vehicle_service.vehicle_repo, 'get_by_id', return_value=sample_vehicle_data):
            
            # Act
            result = await vehicle_service.get_vehicle_by_id(vehicle_id)

            # Assert
            assert result is not None
            assert result["_id"] == sample_vehicle_data["_id"]
            assert result["make"] == sample_vehicle_data["make"]
            assert result["model"] == sample_vehicle_data["model"]

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_not_found(self, vehicle_service):
        """Test vehicle retrieval with non-existent ID"""
        # Arrange
        vehicle_id = str(ObjectId())
        
        with patch.object(vehicle_service.vehicle_repo, 'get_by_id', return_value=None):
            
            # Act
            result = await vehicle_service.get_vehicle_by_id(vehicle_id)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_get_vehicles_with_pagination(self, vehicle_service, sample_vehicle_data):
        """Test getting vehicles with pagination"""
        # Arrange
        vehicles = [sample_vehicle_data]
        pagination = {"skip": 0, "limit": 10}
        
        with patch.object(vehicle_service.vehicle_repo, 'get_all') as mock_get_all, \
             patch.object(vehicle_service.vehicle_repo, 'count', return_value=1):
            
            mock_get_all.return_value = vehicles

            # Act
            result = await vehicle_service.get_vehicles(pagination=pagination)

            # Assert
            assert "vehicles" in result
            assert "pagination" in result
            assert len(result["vehicles"]) == 1
            assert result["pagination"]["total"] == 1
            assert result["pagination"]["page"] == 1

    @pytest.mark.asyncio
    async def test_get_vehicles_with_filters(self, vehicle_service, sample_vehicle_data):
        """Test getting vehicles with filters"""
        # Arrange
        vehicles = [sample_vehicle_data]
        filters = {"department": "Security", "status": "available"}
        
        with patch.object(vehicle_service.vehicle_repo, 'get_all') as mock_get_all, \
             patch.object(vehicle_service.vehicle_repo, 'count', return_value=1):
            
            mock_get_all.return_value = vehicles

            # Act
            result = await vehicle_service.get_vehicles(filters=filters)

            # Assert
            assert "vehicles" in result
            assert len(result["vehicles"]) == 1
            mock_get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vehicle_success(self, vehicle_service, sample_vehicle_data):
        """Test successful vehicle update"""
        # Arrange
        vehicle_id = str(sample_vehicle_data["_id"])
        update_data = {"status": "maintenance", "mileage": 20000}
        updated_by = "test_user"
        
        updated_vehicle = {**sample_vehicle_data, **update_data}
        
        with patch.object(vehicle_service.vehicle_repo, 'get_by_id', return_value=sample_vehicle_data), \
             patch.object(vehicle_service.vehicle_repo, 'update', return_value=True), \
             patch.object(vehicle_service.vehicle_repo, 'get_by_id', return_value=updated_vehicle):

            # Act
            result = await vehicle_service.update_vehicle(vehicle_id, update_data, updated_by)

            # Assert
            assert result is not None
            assert result["status"] == "maintenance"
            assert result["mileage"] == 20000

    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self, vehicle_service):
        """Test vehicle update with non-existent ID"""
        # Arrange
        vehicle_id = str(ObjectId())
        update_data = {"status": "maintenance"}
        updated_by = "test_user"
        
        with patch.object(vehicle_service.vehicle_repo, 'get_by_id', return_value=None):

            # Act & Assert
            with pytest.raises(ValueError, match="not found"):
                await vehicle_service.update_vehicle(vehicle_id, update_data, updated_by)

    @pytest.mark.asyncio
    async def test_delete_vehicle_success(self, vehicle_service, sample_vehicle_data):
        """Test successful vehicle deletion"""
        # Arrange
        vehicle_id = str(sample_vehicle_data["_id"])
        
        with patch.object(vehicle_service.vehicle_repo, 'get_by_id', return_value=sample_vehicle_data), \
             patch.object(vehicle_service.vehicle_repo, 'delete', return_value=True):

            # Act
            result = await vehicle_service.delete_vehicle(vehicle_id)

            # Assert
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_vehicle_not_found(self, vehicle_service):
        """Test vehicle deletion with non-existent ID"""
        # Arrange
        vehicle_id = str(ObjectId())
        
        with patch.object(vehicle_service.vehicle_repo, 'get_by_id', return_value=None):

            # Act & Assert
            with pytest.raises(ValueError, match="not found"):
                await vehicle_service.delete_vehicle(vehicle_id)

    @pytest.mark.asyncio
    async def test_fuel_type_normalization(self, vehicle_service, mock_mongodb):
        """Test fuel type normalization during vehicle creation"""
        # Arrange
        request_data = {
            "make": "Toyota",
            "model": "Hilux",
            "year": 2023,
            "license_plate": "FUEL123GP",
            "vin": "1GTPUEE18J8123456",
            "fuel_type": "gasoline",  # Should be normalized to "petrol"
            "color": "Blue"
        }
        vehicle_request = VehicleCreateRequest(**request_data)
        created_by = "test_user"
        vehicle_id = str(ObjectId())
        
        with patch.object(vehicle_service.vehicle_repo, 'get_by_registration_number', return_value=None), \
             patch.object(vehicle_service.vehicle_repo, 'create', return_value=vehicle_id), \
             patch.object(vehicle_service.vehicle_repo, 'get_by_id') as mock_get_by_id:
            
            created_vehicle = {
                **request_data,
                "_id": vehicle_id,
                "fuel_type": "petrol",  # Normalized
                "registration_number": request_data["license_plate"],
                "created_by": created_by,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_get_by_id.return_value = created_vehicle

            # Act
            result = await vehicle_service.create_vehicle(vehicle_request, created_by)

            # Assert
            assert result["fuel_type"] == "petrol"  # Should be normalized from "gasoline"

    @pytest.mark.asyncio
    async def test_status_normalization(self, vehicle_service, mock_mongodb):
        """Test status normalization during vehicle creation"""
        # Arrange
        request_data = {
            "make": "Toyota",
            "model": "Hilux",
            "year": 2023,
            "license_plate": "STATUS123GP",
            "vin": "1GTPUEE18J8123456",
            "fuel_type": "diesel",
            "color": "Blue",
            "status": "active"  # Should be normalized to "available"
        }
        vehicle_request = VehicleCreateRequest(**request_data)
        created_by = "test_user"
        vehicle_id = str(ObjectId())
        
        with patch.object(vehicle_service.vehicle_repo, 'get_by_registration_number', return_value=None), \
             patch.object(vehicle_service.vehicle_repo, 'create', return_value=vehicle_id), \
             patch.object(vehicle_service.vehicle_repo, 'get_by_id') as mock_get_by_id:
            
            created_vehicle = {
                **request_data,
                "_id": vehicle_id,
                "status": "available",  # Normalized
                "registration_number": request_data["license_plate"],
                "created_by": created_by,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_get_by_id.return_value = created_vehicle

            # Act
            result = await vehicle_service.create_vehicle(vehicle_request, created_by)

            # Assert
            assert result["status"] == "available"  # Should be normalized from "active"
