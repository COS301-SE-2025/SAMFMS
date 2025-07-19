"""
Unit tests for repositories module
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from repositories.repositories import (
    VehicleRepository,
    DriverRepository,
    VehicleAssignmentRepository,
    AnalyticsRepository
)


@pytest.mark.unit
@pytest.mark.repository
class TestVehicleRepository:
    """Test class for VehicleRepository"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_collection = AsyncMock()
        self.repository = VehicleRepository()
        # Mock the collection property
        self.repository.collection = self.mock_collection
        
        # Mock vehicle data
        self.vehicle_id = ObjectId()
        self.vehicle_data = {
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
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    
    @pytest.mark.asyncio
    async def test_get_by_registration_number_found(self):
        """Test getting vehicle by registration number when found"""
        # Arrange
        registration_number = "ABC-001"
        self.mock_collection.find_one.return_value = self.vehicle_data
        
        # Act
        result = await self.repository.get_by_registration_number(registration_number)
        
        # Assert
        assert result == self.vehicle_data
        self.mock_collection.find_one.assert_called_once_with(
            {"registration_number": registration_number}
        )
    
    @pytest.mark.asyncio
    async def test_get_by_registration_number_not_found(self):
        """Test getting vehicle by registration number when not found"""
        # Arrange
        registration_number = "XYZ-999"
        self.mock_collection.find_one.return_value = None
        
        # Act
        result = await self.repository.get_by_registration_number(registration_number)
        
        # Assert
        assert result is None
        self.mock_collection.find_one.assert_called_once_with(
            {"registration_number": registration_number}
        )
    
    @pytest.mark.asyncio
    async def test_get_by_license_plate_found(self):
        """Test getting vehicle by license plate when found"""
        # Arrange
        license_plate = "ABC001"
        self.mock_collection.find_one.return_value = self.vehicle_data
        
        # Act
        result = await self.repository.get_by_license_plate(license_plate)
        
        # Assert
        assert result == self.vehicle_data
        self.mock_collection.find_one.assert_called_once_with(
            {"license_plate": license_plate}
        )
    
    @pytest.mark.asyncio
    async def test_get_by_department_success(self):
        """Test getting vehicles by department"""
        # Arrange
        department = "operations"
        vehicles = [self.vehicle_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = vehicles
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_by_department(department)
        
        # Assert
        assert result == vehicles
        self.mock_collection.find.assert_called_once_with({"department": department})
    
    @pytest.mark.asyncio
    async def test_get_available_vehicles_success(self):
        """Test getting available vehicles"""
        # Arrange
        available_vehicles = [self.vehicle_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = available_vehicles
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_available_vehicles()
        
        # Assert
        assert result == available_vehicles
        self.mock_collection.find.assert_called_once_with({"status": "available"})
    
    @pytest.mark.asyncio
    async def test_get_vehicles_by_status_success(self):
        """Test getting vehicles by status"""
        # Arrange
        status = "maintenance"
        vehicles = [self.vehicle_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = vehicles
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_vehicles_by_status(status)
        
        # Assert
        assert result == vehicles
        self.mock_collection.find.assert_called_once_with({"status": status})
    
    @pytest.mark.asyncio
    async def test_search_vehicles_success(self):
        """Test searching vehicles"""
        # Arrange
        search_query = "Toyota"
        vehicles = [self.vehicle_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = vehicles
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.search_vehicles(search_query)
        
        # Assert
        assert result == vehicles
        self.mock_collection.find.assert_called_once()
        
        # Check that search query was used in $or condition
        call_args = self.mock_collection.find.call_args[0][0]
        assert "$or" in call_args
    
    @pytest.mark.asyncio
    async def test_get_vehicles_by_fuel_type_success(self):
        """Test getting vehicles by fuel type"""
        # Arrange
        fuel_type = "petrol"
        vehicles = [self.vehicle_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = vehicles
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_vehicles_by_fuel_type(fuel_type)
        
        # Assert
        assert result == vehicles
        self.mock_collection.find.assert_called_once_with({"fuel_type": fuel_type})
    
    @pytest.mark.asyncio
    async def test_get_vehicles_by_year_range_success(self):
        """Test getting vehicles by year range"""
        # Arrange
        min_year = 2020
        max_year = 2024
        vehicles = [self.vehicle_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = vehicles
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_vehicles_by_year_range(min_year, max_year)
        
        # Assert
        assert result == vehicles
        self.mock_collection.find.assert_called_once_with(
            {"year": {"$gte": min_year, "$lte": max_year}}
        )
    
    @pytest.mark.asyncio
    async def test_get_vehicles_by_mileage_range_success(self):
        """Test getting vehicles by mileage range"""
        # Arrange
        min_mileage = 10000
        max_mileage = 20000
        vehicles = [self.vehicle_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = vehicles
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_vehicles_by_mileage_range(min_mileage, max_mileage)
        
        # Assert
        assert result == vehicles
        self.mock_collection.find.assert_called_once_with(
            {"mileage": {"$gte": min_mileage, "$lte": max_mileage}}
        )
    
    @pytest.mark.asyncio
    async def test_update_vehicle_status_success(self):
        """Test updating vehicle status"""
        # Arrange
        vehicle_id = str(self.vehicle_id)
        new_status = "in_use"
        
        mock_result = AsyncMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Act
        result = await self.repository.update_vehicle_status(vehicle_id, new_status)
        
        # Assert
        assert result is True
        self.mock_collection.update_one.assert_called_once()
        
        # Check update parameters
        call_args = self.mock_collection.update_one.call_args
        assert call_args[0][0] == {"_id": ObjectId(vehicle_id)}
        assert call_args[0][1]["$set"]["status"] == new_status
        assert "updated_at" in call_args[0][1]["$set"]
    
    @pytest.mark.asyncio
    async def test_update_vehicle_mileage_success(self):
        """Test updating vehicle mileage"""
        # Arrange
        vehicle_id = str(self.vehicle_id)
        new_mileage = 16000
        
        mock_result = AsyncMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Act
        result = await self.repository.update_vehicle_mileage(vehicle_id, new_mileage)
        
        # Assert
        assert result is True
        self.mock_collection.update_one.assert_called_once()
        
        # Check update parameters
        call_args = self.mock_collection.update_one.call_args
        assert call_args[0][0] == {"_id": ObjectId(vehicle_id)}
        assert call_args[0][1]["$set"]["mileage"] == new_mileage
        assert "updated_at" in call_args[0][1]["$set"]


@pytest.mark.unit
@pytest.mark.repository
class TestDriverRepository:
    """Test class for DriverRepository"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_collection = AsyncMock()
        self.repository = DriverRepository()
        # Mock the collection property
        self.repository.collection = self.mock_collection
        
        # Mock driver data
        self.driver_id = ObjectId()
        self.driver_data = {
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
    async def test_get_by_employee_id_found(self):
        """Test getting driver by employee ID when found"""
        # Arrange
        employee_id = "EMP001"
        self.mock_collection.find_one.return_value = self.driver_data
        
        # Act
        result = await self.repository.get_by_employee_id(employee_id)
        
        # Assert
        assert result == self.driver_data
        self.mock_collection.find_one.assert_called_once_with(
            {"employee_id": employee_id}
        )
    
    @pytest.mark.asyncio
    async def test_get_by_employee_id_not_found(self):
        """Test getting driver by employee ID when not found"""
        # Arrange
        employee_id = "EMP999"
        self.mock_collection.find_one.return_value = None
        
        # Act
        result = await self.repository.get_by_employee_id(employee_id)
        
        # Assert
        assert result is None
        self.mock_collection.find_one.assert_called_once_with(
            {"employee_id": employee_id}
        )
    
    @pytest.mark.asyncio
    async def test_get_by_license_number_found(self):
        """Test getting driver by license number when found"""
        # Arrange
        license_number = "DL123456789"
        self.mock_collection.find_one.return_value = self.driver_data
        
        # Act
        result = await self.repository.get_by_license_number(license_number)
        
        # Assert
        assert result == self.driver_data
        self.mock_collection.find_one.assert_called_once_with(
            {"license_number": license_number}
        )
    
    @pytest.mark.asyncio
    async def test_get_by_department_success(self):
        """Test getting drivers by department"""
        # Arrange
        department = "operations"
        drivers = [self.driver_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = drivers
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_by_department(department)
        
        # Assert
        assert result == drivers
        self.mock_collection.find.assert_called_once_with({"department": department})
    
    @pytest.mark.asyncio
    async def test_get_active_drivers_success(self):
        """Test getting active drivers"""
        # Arrange
        active_drivers = [self.driver_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = active_drivers
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_active_drivers()
        
        # Assert
        assert result == active_drivers
        self.mock_collection.find.assert_called_once_with({"status": "active"})
    
    @pytest.mark.asyncio
    async def test_get_drivers_by_status_success(self):
        """Test getting drivers by status"""
        # Arrange
        status = "inactive"
        drivers = [self.driver_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = drivers
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_drivers_by_status(status)
        
        # Assert
        assert result == drivers
        self.mock_collection.find.assert_called_once_with({"status": status})
    
    @pytest.mark.asyncio
    async def test_search_drivers_success(self):
        """Test searching drivers"""
        # Arrange
        search_query = "John"
        drivers = [self.driver_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = drivers
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.search_drivers(search_query)
        
        # Assert
        assert result == drivers
        self.mock_collection.find.assert_called_once()
        
        # Check that search query was used in $or condition
        call_args = self.mock_collection.find.call_args[0][0]
        assert "$or" in call_args
    
    @pytest.mark.asyncio
    async def test_get_drivers_by_license_class_success(self):
        """Test getting drivers by license class"""
        # Arrange
        license_class = "B"
        drivers = [self.driver_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = drivers
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_drivers_by_license_class(license_class)
        
        # Assert
        assert result == drivers
        self.mock_collection.find.assert_called_once_with({"license_class": license_class})
    
    @pytest.mark.asyncio
    async def test_get_drivers_with_expiring_licenses_success(self):
        """Test getting drivers with expiring licenses"""
        # Arrange
        expiry_date = datetime.now(timezone.utc)
        drivers = [self.driver_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = drivers
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_drivers_with_expiring_licenses(expiry_date)
        
        # Assert
        assert result == drivers
        self.mock_collection.find.assert_called_once_with(
            {"license_expiry": {"$lte": expiry_date}}
        )
    
    @pytest.mark.asyncio
    async def test_update_driver_status_success(self):
        """Test updating driver status"""
        # Arrange
        driver_id = str(self.driver_id)
        new_status = "inactive"
        
        mock_result = AsyncMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Act
        result = await self.repository.update_driver_status(driver_id, new_status)
        
        # Assert
        assert result is True
        self.mock_collection.update_one.assert_called_once()
        
        # Check update parameters
        call_args = self.mock_collection.update_one.call_args
        assert call_args[0][0] == {"_id": ObjectId(driver_id)}
        assert call_args[0][1]["$set"]["status"] == new_status
        assert "updated_at" in call_args[0][1]["$set"]


@pytest.mark.unit
@pytest.mark.repository
class TestVehicleAssignmentRepository:
    """Test class for VehicleAssignmentRepository"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_collection = AsyncMock()
        self.repository = VehicleAssignmentRepository()
        # Mock the collection property
        self.repository.collection = self.mock_collection
        
        # Mock assignment data
        self.assignment_id = ObjectId()
        self.assignment_data = {
            "_id": self.assignment_id,
            "vehicle_id": ObjectId(),
            "driver_id": ObjectId(),
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
    async def test_get_by_vehicle_id_success(self):
        """Test getting assignments by vehicle ID"""
        # Arrange
        vehicle_id = str(ObjectId())
        assignments = [self.assignment_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = assignments
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_by_vehicle_id(vehicle_id)
        
        # Assert
        assert result == assignments
        self.mock_collection.find.assert_called_once_with(
            {"vehicle_id": ObjectId(vehicle_id)}
        )
    
    @pytest.mark.asyncio
    async def test_get_by_driver_id_success(self):
        """Test getting assignments by driver ID"""
        # Arrange
        driver_id = str(ObjectId())
        assignments = [self.assignment_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = assignments
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_by_driver_id(driver_id)
        
        # Assert
        assert result == assignments
        self.mock_collection.find.assert_called_once_with(
            {"driver_id": ObjectId(driver_id)}
        )
    
    @pytest.mark.asyncio
    async def test_get_active_assignments_success(self):
        """Test getting active assignments"""
        # Arrange
        active_assignments = [self.assignment_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = active_assignments
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_active_assignments()
        
        # Assert
        assert result == active_assignments
        self.mock_collection.find.assert_called_once_with({"status": "active"})
    
    @pytest.mark.asyncio
    async def test_get_assignments_by_status_success(self):
        """Test getting assignments by status"""
        # Arrange
        status = "completed"
        assignments = [self.assignment_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = assignments
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_assignments_by_status(status)
        
        # Assert
        assert result == assignments
        self.mock_collection.find.assert_called_once_with({"status": status})
    
    @pytest.mark.asyncio
    async def test_get_assignments_by_type_success(self):
        """Test getting assignments by type"""
        # Arrange
        assignment_type = "temporary"
        assignments = [self.assignment_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = assignments
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_assignments_by_type(assignment_type)
        
        # Assert
        assert result == assignments
        self.mock_collection.find.assert_called_once_with(
            {"assignment_type": assignment_type}
        )
    
    @pytest.mark.asyncio
    async def test_get_assignments_by_date_range_success(self):
        """Test getting assignments by date range"""
        # Arrange
        start_date = datetime.now(timezone.utc)
        end_date = datetime.now(timezone.utc)
        assignments = [self.assignment_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = assignments
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_assignments_by_date_range(start_date, end_date)
        
        # Assert
        assert result == assignments
        self.mock_collection.find.assert_called_once_with({
            "start_date": {"$gte": start_date, "$lte": end_date}
        })
    
    @pytest.mark.asyncio
    async def test_get_current_assignment_for_vehicle_success(self):
        """Test getting current assignment for vehicle"""
        # Arrange
        vehicle_id = str(ObjectId())
        self.mock_collection.find_one.return_value = self.assignment_data
        
        # Act
        result = await self.repository.get_current_assignment_for_vehicle(vehicle_id)
        
        # Assert
        assert result == self.assignment_data
        self.mock_collection.find_one.assert_called_once_with({
            "vehicle_id": ObjectId(vehicle_id),
            "status": "active"
        })
    
    @pytest.mark.asyncio
    async def test_get_current_assignment_for_driver_success(self):
        """Test getting current assignment for driver"""
        # Arrange
        driver_id = str(ObjectId())
        self.mock_collection.find_one.return_value = self.assignment_data
        
        # Act
        result = await self.repository.get_current_assignment_for_driver(driver_id)
        
        # Assert
        assert result == self.assignment_data
        self.mock_collection.find_one.assert_called_once_with({
            "driver_id": ObjectId(driver_id),
            "status": "active"
        })
    
    @pytest.mark.asyncio
    async def test_update_assignment_status_success(self):
        """Test updating assignment status"""
        # Arrange
        assignment_id = str(self.assignment_id)
        new_status = "completed"
        
        mock_result = AsyncMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Act
        result = await self.repository.update_assignment_status(assignment_id, new_status)
        
        # Assert
        assert result is True
        self.mock_collection.update_one.assert_called_once()
        
        # Check update parameters
        call_args = self.mock_collection.update_one.call_args
        assert call_args[0][0] == {"_id": ObjectId(assignment_id)}
        assert call_args[0][1]["$set"]["status"] == new_status
        assert "updated_at" in call_args[0][1]["$set"]


@pytest.mark.unit
@pytest.mark.repository
class TestAnalyticsRepository:
    """Test class for AnalyticsRepository"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_collection = AsyncMock()
        self.repository = AnalyticsRepository()
        # Mock the collection property
        self.repository.collection = self.mock_collection
        
        # Mock analytics data
        self.analytics_id = ObjectId()
        self.analytics_data = {
            "_id": self.analytics_id,
            "metric_type": "fleet_utilization",
            "metric_value": 85.5,
            "period": "daily",
            "department": "operations",
            "generated_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    
    @pytest.mark.asyncio
    async def test_get_by_metric_type_success(self):
        """Test getting analytics by metric type"""
        # Arrange
        metric_type = "fleet_utilization"
        analytics = [self.analytics_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = analytics
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_by_metric_type(metric_type)
        
        # Assert
        assert result == analytics
        self.mock_collection.find.assert_called_once_with(
            {"metric_type": metric_type}
        )
    
    @pytest.mark.asyncio
    async def test_get_by_period_success(self):
        """Test getting analytics by period"""
        # Arrange
        period = "daily"
        analytics = [self.analytics_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = analytics
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_by_period(period)
        
        # Assert
        assert result == analytics
        self.mock_collection.find.assert_called_once_with({"period": period})
    
    @pytest.mark.asyncio
    async def test_get_by_department_success(self):
        """Test getting analytics by department"""
        # Arrange
        department = "operations"
        analytics = [self.analytics_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = analytics
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_by_department(department)
        
        # Assert
        assert result == analytics
        self.mock_collection.find.assert_called_once_with({"department": department})
    
    @pytest.mark.asyncio
    async def test_get_by_date_range_success(self):
        """Test getting analytics by date range"""
        # Arrange
        start_date = datetime.now(timezone.utc)
        end_date = datetime.now(timezone.utc)
        analytics = [self.analytics_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = analytics
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_by_date_range(start_date, end_date)
        
        # Assert
        assert result == analytics
        self.mock_collection.find.assert_called_once_with({
            "generated_at": {"$gte": start_date, "$lte": end_date}
        })
    
    @pytest.mark.asyncio
    async def test_get_latest_metrics_success(self):
        """Test getting latest metrics"""
        # Arrange
        analytics = [self.analytics_data]
        mock_cursor = AsyncMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list.return_value = analytics
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_latest_metrics()
        
        # Assert
        assert result == analytics
        self.mock_collection.find.assert_called_once_with({})
        mock_cursor.sort.assert_called_once_with("generated_at", -1)
        mock_cursor.limit.assert_called_once_with(10)
    
    @pytest.mark.asyncio
    async def test_get_expired_metrics_success(self):
        """Test getting expired metrics"""
        # Arrange
        current_time = datetime.now(timezone.utc)
        analytics = [self.analytics_data]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = analytics
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_expired_metrics(current_time)
        
        # Assert
        assert result == analytics
        self.mock_collection.find.assert_called_once_with({
            "expires_at": {"$lte": current_time}
        })
    
    @pytest.mark.asyncio
    async def test_delete_expired_metrics_success(self):
        """Test deleting expired metrics"""
        # Arrange
        current_time = datetime.now(timezone.utc)
        
        mock_result = AsyncMock()
        mock_result.deleted_count = 5
        self.mock_collection.delete_many.return_value = mock_result
        
        # Act
        result = await self.repository.delete_expired_metrics(current_time)
        
        # Assert
        assert result == 5
        self.mock_collection.delete_many.assert_called_once_with({
            "expires_at": {"$lte": current_time}
        })
    
    @pytest.mark.asyncio
    async def test_aggregate_metrics_success(self):
        """Test aggregating metrics"""
        # Arrange
        pipeline = [
            {"$match": {"metric_type": "fleet_utilization"}},
            {"$group": {"_id": "$period", "avg_value": {"$avg": "$metric_value"}}}
        ]
        
        aggregation_result = [
            {"_id": "daily", "avg_value": 85.5},
            {"_id": "weekly", "avg_value": 82.3}
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = aggregation_result
        self.mock_collection.aggregate.return_value = mock_cursor
        
        # Act
        result = await self.repository.aggregate_metrics(pipeline)
        
        # Assert
        assert result == aggregation_result
        self.mock_collection.aggregate.assert_called_once_with(pipeline)
    
    @pytest.mark.asyncio
    async def test_get_metrics_summary_success(self):
        """Test getting metrics summary"""
        # Arrange
        summary_pipeline = [
            {"$group": {
                "_id": "$metric_type",
                "count": {"$sum": 1},
                "avg_value": {"$avg": "$metric_value"},
                "min_value": {"$min": "$metric_value"},
                "max_value": {"$max": "$metric_value"}
            }}
        ]
        
        summary_result = [
            {
                "_id": "fleet_utilization",
                "count": 10,
                "avg_value": 85.5,
                "min_value": 70.0,
                "max_value": 95.0
            }
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = summary_result
        self.mock_collection.aggregate.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_metrics_summary()
        
        # Assert
        assert result == summary_result
        self.mock_collection.aggregate.assert_called_once()
        
        # Check that aggregation pipeline was used
        call_args = self.mock_collection.aggregate.call_args[0][0]
        assert "$group" in call_args[0]


@pytest.mark.unit
@pytest.mark.repository
class TestRepositoryIntegration:
    """Test class for repository integration scenarios"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_vehicle_collection = AsyncMock()
        self.mock_driver_collection = AsyncMock()
        self.mock_assignment_collection = AsyncMock()
        
        self.vehicle_repo = VehicleRepository()
        self.driver_repo = DriverRepository()
        self.assignment_repo = VehicleAssignmentRepository()
        
        # Mock the collection properties
        self.vehicle_repo.collection = self.mock_vehicle_collection
        self.driver_repo.collection = self.mock_driver_collection
        self.assignment_repo.collection = self.mock_assignment_collection
    
    @pytest.mark.asyncio
    async def test_cross_repository_operations(self):
        """Test operations across multiple repositories"""
        # Arrange
        vehicle_id = ObjectId()
        driver_id = ObjectId()
        assignment_id = ObjectId()
        
        # Mock vehicle data
        vehicle_data = {
            "_id": vehicle_id,
            "registration_number": "ABC-001",
            "status": "available"
        }
        
        # Mock driver data
        driver_data = {
            "_id": driver_id,
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "status": "active"
        }
        
        # Mock assignment data
        assignment_data = {
            "_id": assignment_id,
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "status": "active"
        }
        
        # Setup mocks
        self.mock_vehicle_collection.find_one.return_value = vehicle_data
        self.mock_driver_collection.find_one.return_value = driver_data
        self.mock_assignment_collection.find_one.return_value = assignment_data
        
        # Act
        vehicle = await self.vehicle_repo.get_by_id(str(vehicle_id))
        driver = await self.driver_repo.get_by_id(str(driver_id))
        assignment = await self.assignment_repo.get_by_id(str(assignment_id))
        
        # Assert
        assert vehicle["_id"] == vehicle_id
        assert driver["_id"] == driver_id
        assert assignment["vehicle_id"] == vehicle_id
        assert assignment["driver_id"] == driver_id
    
    @pytest.mark.asyncio
    async def test_repository_transaction_scenario(self):
        """Test transaction-like scenario across repositories"""
        # Arrange
        vehicle_id = str(ObjectId())
        driver_id = str(ObjectId())
        
        # Mock successful updates
        mock_vehicle_result = AsyncMock()
        mock_vehicle_result.modified_count = 1
        self.mock_vehicle_collection.update_one.return_value = mock_vehicle_result
        
        mock_driver_result = AsyncMock()
        mock_driver_result.modified_count = 1
        self.mock_driver_collection.update_one.return_value = mock_driver_result
        
        mock_assignment_result = AsyncMock()
        mock_assignment_result.inserted_id = ObjectId()
        self.mock_assignment_collection.insert_one.return_value = mock_assignment_result
        
        # Act - Simulate assignment creation process
        vehicle_updated = await self.vehicle_repo.update_vehicle_status(vehicle_id, "in_use")
        driver_updated = await self.driver_repo.update_driver_status(driver_id, "assigned")
        assignment_created = await self.assignment_repo.create({
            "vehicle_id": ObjectId(vehicle_id),
            "driver_id": ObjectId(driver_id),
            "status": "active"
        })
        
        # Assert
        assert vehicle_updated is True
        assert driver_updated is True
        assert assignment_created is not None
    
    @pytest.mark.asyncio
    async def test_repository_error_handling_across_operations(self):
        """Test error handling across repository operations"""
        # Arrange
        vehicle_id = str(ObjectId())
        
        # Mock vehicle update success
        mock_vehicle_result = AsyncMock()
        mock_vehicle_result.modified_count = 1
        self.mock_vehicle_collection.update_one.return_value = mock_vehicle_result
        
        # Mock driver update failure
        self.mock_driver_collection.update_one.side_effect = Exception("Database error")
        
        # Act & Assert
        vehicle_updated = await self.vehicle_repo.update_vehicle_status(vehicle_id, "in_use")
        assert vehicle_updated is True
        
        with pytest.raises(Exception):
            await self.driver_repo.update_driver_status(str(ObjectId()), "assigned")
    
    @pytest.mark.asyncio
    async def test_repository_performance_with_large_datasets(self):
        """Test repository performance with large datasets"""
        # Arrange
        large_vehicle_list = [
            {"_id": ObjectId(), "registration_number": f"ABC-{i:03d}"}
            for i in range(1000)
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = large_vehicle_list
        self.mock_vehicle_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.vehicle_repo.get_all()
        
        # Assert
        assert len(result) == 1000
        assert result[0]["registration_number"] == "ABC-000"
        assert result[999]["registration_number"] == "ABC-999"
    
    @pytest.mark.asyncio
    async def test_repository_concurrent_operations(self):
        """Test concurrent repository operations"""
        # Arrange
        vehicle_ids = [str(ObjectId()) for _ in range(5)]
        
        # Mock update results
        mock_result = AsyncMock()
        mock_result.modified_count = 1
        self.mock_vehicle_collection.update_one.return_value = mock_result
        
        # Act - Simulate concurrent status updates
        import asyncio
        tasks = [
            self.vehicle_repo.update_vehicle_status(vehicle_id, "maintenance")
            for vehicle_id in vehicle_ids
        ]
        results = await asyncio.gather(*tasks)
        
        # Assert
        assert all(result is True for result in results)
        assert self.mock_vehicle_collection.update_one.call_count == 5
