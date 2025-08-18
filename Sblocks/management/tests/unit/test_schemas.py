"""
Unit tests for schema models
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from bson import ObjectId

from schemas.entities import (
    VehicleAssignment,
    VehicleUsageLog,
    Driver,
    AnalyticsSnapshot,
    AuditLog,
    AssignmentStatus,
    AssignmentType,
    DriverStatus,
    LicenseClass
)
from schemas.requests import VehicleCreateRequest, VehicleUpdateRequest, DriverCreateRequest, DriverUpdateRequest
from schemas.responses import StandardResponse, ErrorResponse


@pytest.mark.unit
@pytest.mark.schemas
class TestEntitySchemas:
    """Test class for entity schema models"""
    
    def test_vehicle_assignment_creation(self):
        """Test VehicleAssignment entity creation"""
        # Arrange
        assignment_data = {
            "vehicle_id": "vehicle123",
            "driver_id": "driver456",
            "assignment_type": AssignmentType.TRIP,
            "status": AssignmentStatus.ACTIVE,
            "start_date": datetime.utcnow(),
            "purpose": "Business trip",
            "created_by": "user123"
        }
        
        # Act
        assignment = VehicleAssignment(**assignment_data)
        
        # Assert
        assert assignment.vehicle_id == "vehicle123"
        assert assignment.driver_id == "driver456"
        assert assignment.assignment_type == AssignmentType.TRIP
        assert assignment.status == AssignmentStatus.ACTIVE
        assert assignment.purpose == "Business trip"
        assert assignment.created_by == "user123"
    
    def test_vehicle_usage_log_creation(self):
        """Test VehicleUsageLog entity creation"""
        # Arrange
        usage_data = {
            "vehicle_id": "vehicle123",
            "driver_id": "driver456",
            "trip_start": datetime.utcnow(),
            "distance_km": 150.5,
            "fuel_consumed": 15.2,
            "purpose": "Client meeting"
        }
        
        # Act
        usage_log = VehicleUsageLog(**usage_data)
        
        # Assert
        assert usage_log.vehicle_id == "vehicle123"
        assert usage_log.driver_id == "driver456"
        assert usage_log.distance_km == 150.5
        assert usage_log.fuel_consumed == 15.2
        assert usage_log.purpose == "Client meeting"
    
    def test_driver_creation(self):
        """Test Driver entity creation"""
        # Arrange
        driver_data = {
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "0123456789",
            "license_number": "1234567890123",
            "license_class": [LicenseClass.EB],
            "license_expiry": datetime.utcnow(),
            "hire_date": datetime.utcnow(),
            "status": DriverStatus.ACTIVE
        }
        
        # Act
        driver = Driver(**driver_data)
        
        # Assert
        assert driver.employee_id == "EMP001"
        assert driver.first_name == "John"
        assert driver.last_name == "Doe"
        assert driver.email == "john.doe@example.com"
        assert driver.phone == "0123456789"
        assert driver.license_number == "1234567890123"
        assert LicenseClass.EB in driver.license_class
        assert driver.status == DriverStatus.ACTIVE
    
    def test_analytics_snapshot_creation(self):
        """Test AnalyticsSnapshot entity creation"""
        # Arrange
        snapshot_data = {
            "metric_type": "fleet_utilization",
            "data": {"total_vehicles": 50, "active_vehicles": 35},
            "expires_at": datetime.utcnow()
        }
        
        # Act
        snapshot = AnalyticsSnapshot(**snapshot_data)
        
        # Assert
        assert snapshot.metric_type == "fleet_utilization"
        assert snapshot.data["total_vehicles"] == 50
        assert snapshot.data["active_vehicles"] == 35
    
    def test_audit_log_creation(self):
        """Test AuditLog entity creation"""
        # Arrange
        audit_data = {
            "entity_type": "vehicle_assignment",
            "entity_id": "assignment123",
            "action": "create",
            "user_id": "user456",
            "changes": {"status": "active"}
        }
        
        # Act
        audit_log = AuditLog(**audit_data)
        
        # Assert
        assert audit_log.entity_type == "vehicle_assignment"
        assert audit_log.entity_id == "assignment123"
        assert audit_log.action == "create"
        assert audit_log.user_id == "user456"
        assert audit_log.changes["status"] == "active"
    
    def test_assignment_status_enum(self):
        """Test AssignmentStatus enum values"""
        # Assert
        assert AssignmentStatus.ACTIVE == "active"
        assert AssignmentStatus.COMPLETED == "completed"
    
    def test_assignment_type_enum(self):
        """Test AssignmentType enum values"""
        # Assert
        assert AssignmentType.TRIP == "trip"
        assert AssignmentType.LONG_TERM == "long_term"
        assert AssignmentType.MAINTENANCE == "maintenance"
    
    def test_driver_status_enum(self):
        """Test DriverStatus enum values"""
        # Assert
        assert DriverStatus.ACTIVE == "active"
        assert DriverStatus.INACTIVE == "inactive"
        assert DriverStatus.SUSPENDED == "suspended"
        assert DriverStatus.ON_LEAVE == "on_leave"
    
    def test_license_class_enum(self):
        """Test LicenseClass enum values"""
        # Assert
        assert LicenseClass.A == "A"
        assert LicenseClass.B == "B"
        assert LicenseClass.C == "C"
        assert LicenseClass.EB == "EB"
        assert LicenseClass.EC == "EC"


@pytest.mark.unit
@pytest.mark.schemas
class TestRequestSchemas:
    """Test class for request schema models"""
    
    def test_vehicle_create_request(self):
        """Test VehicleCreateRequest schema"""
        # Arrange
        request_data = {
            "registration_number": "ABC123GP",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "type": "sedan",
            "fuel_type": "petrol",
            "color": "white"
        }
        
        # Act
        request = VehicleCreateRequest(**request_data)
        
        # Assert
        assert request.registration_number == "ABC123GP"
        assert request.make == "Toyota"
        assert request.model == "Corolla"
        assert request.year == 2022
        assert request.type == "sedan"
        assert request.fuel_type == "petrol"
        assert request.color == "white"
    
    def test_vehicle_update_request(self):
        """Test VehicleUpdateRequest schema"""
        # Arrange
        request_data = {
            "status": "maintenance",
            "mileage": 50000,
            "fuel_type": "diesel"
        }
        
        # Act
        request = VehicleUpdateRequest(**request_data)
        
        # Assert
        assert request.status == "maintenance"
        assert request.mileage == 50000
        assert request.fuel_type == "diesel"
  
    def test_driver_update_request(self):
        """Test DriverUpdateRequest schema"""
        # Arrange
        request_data = {
            "phone": "0987654321",
            "status": DriverStatus.INACTIVE,
            "department": "Operations"
        }
        
        # Act
        request = DriverUpdateRequest(**request_data)
        
        # Assert
        assert request.phone == "0987654321"
        assert request.status == DriverStatus.INACTIVE
        assert request.department == "Operations"
    
    def test_vehicle_create_request_fuel_type_validation(self):
        """Test VehicleCreateRequest fuel type validation"""
        # Arrange
        request_data = {
            "registration_number": "ABC123GP",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "fuel_type": "gasoline"  # Should be normalized to "petrol"
        }
        
        # Act
        request = VehicleCreateRequest(**request_data)
        
        # Assert
        assert request.fuel_type == "petrol"
    
    def test_vehicle_create_request_status_validation(self):
        """Test VehicleCreateRequest status validation"""
        # Arrange
        request_data = {
            "registration_number": "ABC123GP",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "status": "active"  # Should be normalized to "available"
        }
        
        # Act
        request = VehicleCreateRequest(**request_data)
        
        # Assert
        assert request.status == "available"
    
    def test_vehicle_update_request_fuel_type_validation(self):
        """Test VehicleUpdateRequest fuel type validation"""
        # Arrange
        request_data = {
            "fuel_type": "gas"  # Should be normalized to "petrol"
        }
        
        # Act
        request = VehicleUpdateRequest(**request_data)
        
        # Assert
        assert request.fuel_type == "petrol"
    
    def test_vehicle_update_request_status_validation(self):
        """Test VehicleUpdateRequest status validation"""
        # Arrange
        request_data = {
            "status": "inactive"  # Should be normalized to "out_of_service"
        }
        
        # Act
        request = VehicleUpdateRequest(**request_data)
        
        # Assert
        assert request.status == "out_of_service"


@pytest.mark.unit
@pytest.mark.schemas
class TestResponseSchemas:
    """Test class for response schema models"""
    
    def test_standard_response_creation(self):
        """Test StandardResponse schema"""
        # Arrange
        response_data = {
            "status": "success",
            "data": {"id": "123", "name": "Test"},
            "message": "Operation successful"
        }
        
        # Act
        response = StandardResponse(**response_data)
        
        # Assert
        assert response.status == "success"
        assert response.data["id"] == "123"
        assert response.data["name"] == "Test"
        assert response.message == "Operation successful"
        assert response.meta is not None
    
    def test_error_response_creation(self):
        """Test ErrorResponse schema"""
        # Arrange
        error_data = {
            "error": "validation_error",
            "message": "Invalid input data",
            "details": {"field": "email", "reason": "invalid_format"}
        }
        
        # Act
        response = ErrorResponse(**error_data)
        
        # Assert
        assert response.status == "error"
        assert response.error == "validation_error"
        assert response.message == "Invalid input data"
        assert response.details["field"] == "email"
        assert response.details["reason"] == "invalid_format"
    
    def test_standard_response_with_pagination(self):
        """Test StandardResponse with pagination metadata"""
        # Arrange
        from schemas.responses import PaginationMeta
        
        pagination = PaginationMeta(
            current_page=1,
            total_pages=10,
            page_size=20,
            total_items=200,
            has_next=True,
            has_previous=False
        )
        
        response_data = {
            "status": "success",
            "data": [{"id": "1"}, {"id": "2"}]
        }
        
        # Act
        response = StandardResponse(**response_data)
        response.meta.pagination = pagination
        
        # Assert
        assert response.status == "success"
        assert len(response.data) == 2
        assert response.meta.pagination.current_page == 1
        assert response.meta.pagination.total_pages == 10
        assert response.meta.pagination.has_next is True
        assert response.meta.pagination.has_previous is False
    
    def test_standard_response_with_links(self):
        """Test StandardResponse with links"""
        # Arrange
        response_data = {
            "status": "success",
            "data": {"id": "123"},
            "links": {
                "self": "/api/vehicles/123",
                "edit": "/api/vehicles/123/edit"
            }
        }
        
        # Act
        response = StandardResponse(**response_data)
        
        # Assert
        assert response.status == "success"
        assert response.links["self"] == "/api/vehicles/123"
        assert response.links["edit"] == "/api/vehicles/123/edit"
    
    def test_error_response_without_details(self):
        """Test ErrorResponse without details"""
        # Arrange
        error_data = {
            "error": "not_found",
            "message": "Resource not found"
        }
        
        # Act
        response = ErrorResponse(**error_data)
        
        # Assert
        assert response.status == "error"
        assert response.error == "not_found"
        assert response.message == "Resource not found"
        assert response.details is None
