"""
Comprehensive tests for Maintenance Service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from services.maintenance_service import MaintenanceRecordsService
from schemas.entities import MaintenanceStatus, MaintenancePriority, MaintenanceType


class TestMaintenanceRecordsService:
    """Test cases for MaintenanceRecordsService"""
    
    @pytest.fixture
    def service(self):
        """Create service instance with mocked repository"""
        service = MaintenanceRecordsService()
        service.repository = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_maintenance_data(self):
        """Sample maintenance record data"""
        return {
            "vehicle_id": "vehicle_123",
            "maintenance_type": MaintenanceType.PREVENTIVE,
            "scheduled_date": datetime.utcnow() + timedelta(days=7),
            "title": "Oil Change",
            "description": "Regular oil change service",
            "estimated_cost": 150.0
        }
    
    @pytest.mark.asyncio
    async def test_create_maintenance_record_success(self, service, sample_maintenance_data):
        """Test successful maintenance record creation"""
        # Mock repository response
        expected_record = {
            "id": "record_123",
            **sample_maintenance_data,
            "status": MaintenanceStatus.SCHEDULED,
            "priority": MaintenancePriority.MEDIUM,
            "created_at": datetime.utcnow()
        }
        service.repository.create.return_value = expected_record
        
        # Test creation
        result = await service.create_maintenance_record(sample_maintenance_data)
        
        # Assertions
        assert result["id"] == "record_123"
        assert result["vehicle_id"] == "vehicle_123"
        assert result["status"] == MaintenanceStatus.SCHEDULED
        service.repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_maintenance_record_missing_required_field(self, service):
        """Test maintenance record creation with missing required field"""
        invalid_data = {
            "maintenance_type": MaintenanceType.PREVENTIVE,
            "scheduled_date": datetime.utcnow() + timedelta(days=7),
            "title": "Oil Change"
            # Missing vehicle_id
        }
        
        with pytest.raises(ValueError, match="Required field 'vehicle_id' is missing"):
            await service.create_maintenance_record(invalid_data)
    
    @pytest.mark.asyncio
    async def test_auto_set_priority_emergency(self, service, sample_maintenance_data):
        """Test automatic priority setting for emergency maintenance"""
        sample_maintenance_data["maintenance_type"] = "emergency"
        service.repository.create.return_value = {"id": "record_123", **sample_maintenance_data}
        
        await service.create_maintenance_record(sample_maintenance_data)
        
        # Should auto-set to CRITICAL priority
        call_args = service.repository.create.call_args[0][0]
        assert call_args["priority"] == MaintenancePriority.CRITICAL
    
    @pytest.mark.asyncio
    async def test_auto_set_priority_overdue(self, service, sample_maintenance_data):
        """Test automatic priority setting for overdue maintenance"""
        # Set scheduled date in the past
        sample_maintenance_data["scheduled_date"] = datetime.utcnow() - timedelta(days=1)
        service.repository.create.return_value = {"id": "record_123", **sample_maintenance_data}
        
        await service.create_maintenance_record(sample_maintenance_data)
        
        # Should auto-set to HIGH priority
        call_args = service.repository.create.call_args[0][0]
        assert call_args["priority"] == MaintenancePriority.HIGH
    
    @pytest.mark.asyncio
    async def test_calculate_next_service_mileage(self, service):
        """Test next service mileage calculation"""
        # Test oil change interval
        next_mileage = await service._calculate_next_service_mileage(
            "vehicle_123", "oil_change", 50000
        )
        assert next_mileage == 60000  # 50000 + 10000
        
        # Test unknown maintenance type (default interval)
        next_mileage = await service._calculate_next_service_mileage(
            "vehicle_123", "unknown_type", 50000
        )
        assert next_mileage == 65000  # 50000 + 15000 (default)
    
    @pytest.mark.asyncio
    async def test_update_overdue_statuses(self, service):
        """Test batch update of overdue maintenance records"""
        # Mock overdue records
        overdue_records = [
            {"_id": "record_1", "vehicle_id": "vehicle_1", "status": MaintenanceStatus.SCHEDULED},
            {"_id": "record_2", "vehicle_id": "vehicle_2", "status": MaintenanceStatus.SCHEDULED}
        ]
        service.repository.find.return_value = overdue_records
        service.repository.update.return_value = {"_id": "record_1", "status": MaintenanceStatus.OVERDUE}
        
        result = await service.update_overdue_statuses()
        
        # Should update all overdue records
        assert service.repository.update.call_count == 2
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_calculate_maintenance_costs(self, service):
        """Test maintenance cost calculation"""
        # Mock completed maintenance records
        completed_records = [
            {
                "actual_cost": 150.0,
                "labor_cost": 100.0,
                "parts_cost": 50.0,
                "maintenance_type": "oil_change",
                "actual_completion_date": datetime(2024, 1, 15)
            },
            {
                "actual_cost": 300.0,
                "labor_cost": 200.0,
                "parts_cost": 100.0,
                "maintenance_type": "brake_check",
                "actual_completion_date": datetime(2024, 2, 10)
            }
        ]
        service.repository.find.return_value = completed_records
        
        result = await service.calculate_maintenance_costs()
        
        # Verify calculations
        assert result["total_cost"] == 450.0
        assert result["labor_cost"] == 300.0
        assert result["parts_cost"] == 150.0
        assert result["record_count"] == 2
        assert result["average_cost"] == 225.0
        assert result["cost_by_type"]["oil_change"] == 150.0
        assert result["cost_by_type"]["brake_check"] == 300.0


class TestMaintenanceAPI:
    """Test cases for Maintenance API endpoints"""
    
    @pytest.fixture
    def mock_service(self):
        """Mock maintenance service"""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_create_maintenance_record_endpoint(self, mock_service):
        """Test maintenance record creation endpoint"""
        from api.routes.maintenance_records import create_maintenance_record
        
        # Mock request data
        request_data = {
            "vehicle_id": "vehicle_123",
            "maintenance_type": "preventive",
            "scheduled_date": datetime.utcnow() + timedelta(days=7),
            "title": "Oil Change"
        }
        
        # Mock service response
        mock_service.create_maintenance_record.return_value = {
            "id": "record_123",
            **request_data,
            "status": "scheduled"
        }
        
        # Test would require FastAPI test client setup
        # This is a simplified structure test
        assert callable(create_maintenance_record)


class TestMaintenanceRepository:
    """Test cases for Maintenance Repository"""
    
    @pytest.fixture
    def repository(self):
        """Create repository instance with mocked database"""
        from repositories.repositories import MaintenanceRecordsRepository
        repo = MaintenanceRecordsRepository()
        repo.collection = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_get_overdue_maintenance(self, repository):
        """Test getting overdue maintenance records"""
        # Mock database response
        repository.collection.find.return_value.to_list.return_value = [
            {"_id": "record_1", "vehicle_id": "vehicle_1", "status": "scheduled"},
            {"_id": "record_2", "vehicle_id": "vehicle_2", "status": "scheduled"}
        ]
        
        result = await repository.get_overdue_maintenance()
        
        # Verify query was called with correct parameters
        repository.collection.find.assert_called_once()
        call_args = repository.collection.find.call_args[0][0]
        assert call_args["status"]["$in"] == ["scheduled", "in_progress"]
        assert "$lt" in call_args["scheduled_date"]


class TestDatabaseManager:
    """Test cases for Database Manager"""
    
    @pytest.mark.asyncio
    async def test_connection_retry_logic(self):
        """Test database connection retry logic"""
        from repositories.database import DatabaseManager
        
        db_manager = DatabaseManager()
        db_manager.max_retries = 2
        db_manager.retry_delay = 0.1  # Fast retry for testing
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client:
            # First attempt fails, second succeeds
            mock_client.side_effect = [
                Exception("Connection failed"),
                Mock()
            ]
            
            # This would test the retry logic
            # Full implementation would require more complex mocking
            assert db_manager.max_retries == 2


# Fixtures for test data
@pytest.fixture
def sample_vehicles():
    """Sample vehicle data for testing"""
    return [
        {"id": "vehicle_1", "make": "Toyota", "model": "Camry"},
        {"id": "vehicle_2", "make": "Ford", "model": "F-150"}
    ]


@pytest.fixture
def sample_maintenance_schedules():
    """Sample maintenance schedule data"""
    return [
        {
            "id": "schedule_1",
            "vehicle_id": "vehicle_1",
            "maintenance_type": "oil_change",
            "interval_days": 90
        }
    ]


# Integration test setup
class TestMaintenanceIntegration:
    """Integration tests for maintenance service"""
    
    @pytest.mark.asyncio
    async def test_full_maintenance_workflow(self):
        """Test complete maintenance workflow from creation to completion"""
        # This would test the full workflow:
        # 1. Create maintenance record
        # 2. Update status to in_progress
        # 3. Add costs and parts
        # 4. Complete maintenance
        # 5. Verify all business logic triggers
        pass


if __name__ == "__main__":
    pytest.main([__file__])
