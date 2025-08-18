"""
Integration tests for Vehicle API endpoints
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from bson import ObjectId

from main import app
from models.vehicle import Vehicle


@pytest.mark.integration
@pytest.mark.vehicle
class TestVehicleAPIEndpoints:
    """Integration tests for vehicle-related API endpoints"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def valid_vehicle_payload(self):
        """Valid vehicle creation payload"""
        return {
            "registration_number": "ABC123GP",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "type": "Sedan",
            "department": "Security",
            "fuel_type": "petrol",
            "status": "available",
            "capacity": 5,
            "mileage": 15000
        }

    @pytest.mark.asyncio
    async def test_create_vehicle_success(self, client, valid_vehicle_payload):
        """Test successful vehicle creation"""
        with patch('services.vehicle_service.VehicleService.create_vehicle') as mock_create:
            # Arrange
            mock_vehicle_id = str(ObjectId())
            mock_create.return_value = mock_vehicle_id

            # Act
            response = await client.post("/api/vehicles/", json=valid_vehicle_payload)

            # Assert
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == mock_vehicle_id
            assert data["message"] == "Vehicle created successfully"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_vehicle_missing_required_field(self, client):
        """Test vehicle creation with missing required field"""
        # Arrange
        invalid_payload = {
            "make": "Toyota",
            "model": "Corolla",
            # Missing registration_number
        }

        # Act
        response = await client.post("/api/vehicles/", json=invalid_payload)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_vehicle_invalid_fuel_type(self, client, valid_vehicle_payload):
        """Test vehicle creation with invalid fuel type"""
        # Arrange
        invalid_payload = valid_vehicle_payload.copy()
        invalid_payload["fuel_type"] = "invalid_fuel"

        # Act
        response = await client.post("/api/vehicles/", json=invalid_payload)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_vehicle_duplicate_registration(self, client, valid_vehicle_payload):
        """Test vehicle creation with duplicate registration number"""
        with patch('services.vehicle_service.VehicleService.create_vehicle') as mock_create:
            # Arrange
            mock_create.side_effect = ValueError("Vehicle with this registration number already exists")

            # Act
            response = await client.post("/api/vehicles/", json=valid_vehicle_payload)

            # Assert
            assert response.status_code == 400
            data = response.json()
            assert "Vehicle with this registration number already exists" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_success(self, client, sample_vehicle_data):
        """Test successful vehicle retrieval by ID"""
        with patch('services.vehicle_service.VehicleService.get_vehicle') as mock_get:
            # Arrange
            vehicle_id = str(sample_vehicle_data["_id"])
            mock_get.return_value = sample_vehicle_data

            # Act
            response = await client.get(f"/api/vehicles/{vehicle_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["_id"] == vehicle_id
            assert data["registration_number"] == sample_vehicle_data["registration_number"]
            mock_get.assert_called_once_with(vehicle_id)

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_not_found(self, client):
        """Test vehicle retrieval with non-existent ID"""
        with patch('services.vehicle_service.VehicleService.get_vehicle') as mock_get:
            # Arrange
            vehicle_id = str(ObjectId())
            mock_get.return_value = None

            # Act
            response = await client.get(f"/api/vehicles/{vehicle_id}")

            # Assert
            assert response.status_code == 404
            data = response.json()
            assert "Vehicle not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_all_vehicles_success(self, client, sample_vehicle_data):
        """Test successful retrieval of all vehicles"""
        with patch('services.vehicle_service.VehicleService.get_all_vehicles') as mock_get_all:
            # Arrange
            vehicles = [sample_vehicle_data]
            mock_get_all.return_value = vehicles

            # Act
            response = await client.get("/api/vehicles/")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["_id"] == str(sample_vehicle_data["_id"])

    @pytest.mark.asyncio
    async def test_get_all_vehicles_with_filters(self, client, sample_vehicle_data):
        """Test vehicle retrieval with query filters"""
        with patch('services.vehicle_service.VehicleService.get_all_vehicles') as mock_get_all:
            # Arrange
            vehicles = [sample_vehicle_data]
            mock_get_all.return_value = vehicles

            # Act
            response = await client.get("/api/vehicles/?department=Security&status=available")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            # Verify that the service was called with filters
            call_args = mock_get_all.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_update_vehicle_success(self, client, sample_vehicle_data):
        """Test successful vehicle update"""
        with patch('services.vehicle_service.VehicleService.update_vehicle') as mock_update:
            # Arrange
            vehicle_id = str(sample_vehicle_data["_id"])
            update_data = {"status": "maintenance", "mileage": 20000}
            updated_vehicle = sample_vehicle_data.copy()
            updated_vehicle.update(update_data)
            mock_update.return_value = updated_vehicle

            # Act
            response = await client.put(f"/api/vehicles/{vehicle_id}", json=update_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "maintenance"
            assert data["mileage"] == 20000
            mock_update.assert_called_once_with(vehicle_id, update_data)

    @pytest.mark.asyncio
    async def test_update_vehicle_not_found(self, client):
        """Test updating non-existent vehicle"""
        with patch('services.vehicle_service.VehicleService.update_vehicle') as mock_update:
            # Arrange
            vehicle_id = str(ObjectId())
            update_data = {"status": "maintenance"}
            mock_update.return_value = None

            # Act
            response = await client.put(f"/api/vehicles/{vehicle_id}", json=update_data)

            # Assert
            assert response.status_code == 404
            data = response.json()
            assert "Vehicle not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_delete_vehicle_success(self, client, sample_vehicle_data):
        """Test successful vehicle deletion"""
        with patch('services.vehicle_service.VehicleService.delete_vehicle') as mock_delete:
            # Arrange
            vehicle_id = str(sample_vehicle_data["_id"])
            mock_delete.return_value = True

            # Act
            response = await client.delete(f"/api/vehicles/{vehicle_id}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "Vehicle deleted successfully" in data["message"]
            mock_delete.assert_called_once_with(vehicle_id)

    @pytest.mark.asyncio
    async def test_delete_vehicle_not_found(self, client):
        """Test deleting non-existent vehicle"""
        with patch('services.vehicle_service.VehicleService.delete_vehicle') as mock_delete:
            # Arrange
            vehicle_id = str(ObjectId())
            mock_delete.return_value = False

            # Act
            response = await client.delete(f"/api/vehicles/{vehicle_id}")

            # Assert
            assert response.status_code == 404
            data = response.json()
            assert "Vehicle not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_vehicles_success(self, client, sample_vehicle_data):
        """Test vehicle search functionality"""
        with patch('services.vehicle_service.VehicleService.search_vehicles') as mock_search:
            # Arrange
            search_term = "Toyota"
            vehicles = [sample_vehicle_data]
            mock_search.return_value = vehicles

            # Act
            response = await client.get(f"/api/vehicles/search?q={search_term}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["make"] == "Toyota"
            mock_search.assert_called_once_with(search_term)

    @pytest.mark.asyncio
    async def test_get_vehicles_by_department_success(self, client, sample_vehicle_data):
        """Test getting vehicles by department"""
        with patch('services.vehicle_service.VehicleService.get_vehicles_by_department') as mock_get_dept:
            # Arrange
            department = "Security"
            vehicles = [sample_vehicle_data]
            mock_get_dept.return_value = vehicles

            # Act
            response = await client.get(f"/api/vehicles/department/{department}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["department"] == department
            mock_get_dept.assert_called_once_with(department)

    @pytest.mark.asyncio
    async def test_get_available_vehicles_success(self, client, sample_vehicle_data):
        """Test getting available vehicles"""
        with patch('services.vehicle_service.VehicleService.get_available_vehicles') as mock_get_available:
            # Arrange
            available_vehicle = sample_vehicle_data.copy()
            available_vehicle["status"] = "available"
            vehicles = [available_vehicle]
            mock_get_available.return_value = vehicles

            # Act
            response = await client.get("/api/vehicles/available")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["status"] == "available"
            mock_get_available.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_error_handling(self, client, valid_vehicle_payload):
        """Test API error handling for service exceptions"""
        with patch('services.vehicle_service.VehicleService.create_vehicle') as mock_create:
            # Arrange
            mock_create.side_effect = Exception("Database connection error")

            # Act
            response = await client.post("/api/vehicles/", json=valid_vehicle_payload)

            # Assert
            assert response.status_code == 500
            data = response.json()
            assert "Internal server error" in data["detail"]

    @pytest.mark.asyncio
    async def test_validation_error_response_format(self, client):
        """Test that validation errors return proper format"""
        # Arrange
        invalid_payload = {
            "registration_number": "",  # Empty string
            "year": "not_a_number",  # Invalid type
            "fuel_type": "invalid_fuel"  # Invalid enum value
        }

        # Act
        response = await client.post("/api/vehicles/", json=invalid_payload)

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        # Should have multiple validation errors
        assert len(data["detail"]) > 1
