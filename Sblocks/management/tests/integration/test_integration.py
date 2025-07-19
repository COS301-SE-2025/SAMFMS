"""
Integration tests for the Management Service API
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId

from services.vehicle_service import VehicleService
from services.driver_service import DriverService
from services.analytics_service import AnalyticsService


@pytest.mark.integration
class TestServiceIntegration:
    """Integration tests for service layer"""
    
    @pytest.mark.asyncio
    async def test_vehicle_service_integration(self):
        """Test vehicle service integration with database and events"""
        # Arrange
        with patch('services.vehicle_service.db_manager') as mock_db_manager, \
             patch('services.vehicle_service.event_publisher') as mock_event_publisher:
            
            # Mock database
            mock_db = MagicMock()
            mock_collection = AsyncMock()
            mock_db_manager.db = mock_db
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            # Mock event publisher
            mock_event_publisher.publish_vehicle_created = AsyncMock()
            mock_event_publisher.publish_vehicle_updated = AsyncMock()
            mock_event_publisher.publish_vehicle_deleted = AsyncMock()
            
            vehicle_service = VehicleService()
            
            # Test data
            vehicle_data = {
                "registration_number": "INT-001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "fuel_type": "petrol",
                "status": "available"
            }
            
            vehicle_id = ObjectId()
            created_vehicle = {
                "_id": vehicle_id,
                **vehicle_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Mock database responses
            mock_collection.insert_one.return_value.inserted_id = vehicle_id
            mock_collection.find_one.return_value = created_vehicle
            mock_collection.update_one.return_value.modified_count = 1
            mock_collection.delete_one.return_value.deleted_count = 1
            
            # Act & Assert
            
            # 1. Create vehicle
            result = await vehicle_service.create_vehicle(vehicle_data)
            assert result is not None
            assert result["registration_number"] == "INT-001"
            mock_event_publisher.publish_vehicle_created.assert_called_once()
            
            # 2. Get vehicle
            result = await vehicle_service.get_vehicle_by_id(str(vehicle_id))
            assert result is not None
            assert result["registration_number"] == "INT-001"
            
            # 3. Update vehicle
            updated_vehicle = {**created_vehicle, "status": "maintenance"}
            mock_collection.find_one.return_value = updated_vehicle
            
            result = await vehicle_service.update_vehicle(str(vehicle_id), {"status": "maintenance"})
            assert result is not None
            mock_event_publisher.publish_vehicle_updated.assert_called_once()
            
            # 4. Delete vehicle
            result = await vehicle_service.delete_vehicle(str(vehicle_id))
            assert result is True
            mock_event_publisher.publish_vehicle_deleted.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_driver_service_integration(self):
        """Test driver service integration with database and events"""
        # Arrange
        with patch('services.driver_service.db_manager') as mock_db_manager, \
             patch('services.driver_service.event_publisher') as mock_event_publisher:
            
            # Mock database
            mock_db = MagicMock()
            mock_collection = AsyncMock()
            mock_db_manager.db = mock_db
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            # Mock event publisher
            mock_event_publisher.publish_driver_created = AsyncMock()
            mock_event_publisher.publish_driver_updated = AsyncMock()
            mock_event_publisher.publish_driver_deleted = AsyncMock()
            
            driver_service = DriverService()
            
            # Test data
            driver_data = {
                "employee_id": "INT-EMP001",
                "first_name": "Integration",
                "last_name": "Test",
                "email": "integration.test@company.com",
                "phone": "+1234567890",
                "license_number": "INT-LIC001",
                "license_class": "C",
                "license_expiry": datetime(2025, 12, 31),
                "hire_date": datetime(2023, 1, 15),
                "status": "active"
            }
            
            driver_id = ObjectId()
            created_driver = {
                "_id": driver_id,
                **driver_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Mock database responses
            mock_collection.insert_one.return_value.inserted_id = driver_id
            mock_collection.find_one.return_value = created_driver
            mock_collection.update_one.return_value.modified_count = 1
            mock_collection.delete_one.return_value.deleted_count = 1
            
            # Act & Assert
            
            # 1. Create driver
            result = await driver_service.create_driver(driver_data)
            assert result is not None
            assert result["employee_id"] == "INT-EMP001"
            mock_event_publisher.publish_driver_created.assert_called_once()
            
            # 2. Get driver
            result = await driver_service.get_driver_by_id(str(driver_id))
            assert result is not None
            assert result["employee_id"] == "INT-EMP001"
            
            # 3. Update driver
            updated_driver = {**created_driver, "status": "inactive"}
            mock_collection.find_one.return_value = updated_driver
            
            result = await driver_service.update_driver(str(driver_id), {"status": "inactive"})
            assert result is not None
            mock_event_publisher.publish_driver_updated.assert_called_once()
            
            # 4. Delete driver
            result = await driver_service.delete_driver(str(driver_id))
            assert result is True
            mock_event_publisher.publish_driver_deleted.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analytics_service_integration(self):
        """Test analytics service integration with repositories"""
        # Arrange
        with patch('services.analytics_service.VehicleRepository') as mock_vehicle_repo, \
             patch('services.analytics_service.DriverRepository') as mock_driver_repo:
            
            # Mock repositories
            mock_vehicle_repo.return_value = AsyncMock()
            mock_driver_repo.return_value = AsyncMock()
            
            analytics_service = AnalyticsService()
            
            # Mock repository responses
            mock_vehicle_repo.return_value.count.return_value = 100
            mock_vehicle_repo.return_value.count_by_status.return_value = {
                "available": 60,
                "in_use": 30,
                "maintenance": 8,
                "out_of_service": 2
            }
            
            mock_driver_repo.return_value.count.return_value = 80
            mock_driver_repo.return_value.count_by_status.return_value = {
                "active": 75,
                "inactive": 5
            }
            
            # Mock additional metrics
            mock_vehicle_repo.return_value.get_utilization_rate.return_value = 0.75
            mock_vehicle_repo.return_value.get_fuel_efficiency_avg.return_value = 12.5
            mock_vehicle_repo.return_value.get_maintenance_rate.return_value = 0.08
            mock_driver_repo.return_value.get_average_performance_score.return_value = 87.5
            mock_driver_repo.return_value.get_license_expiry_warnings.return_value = 3
            
            # Act
            result = await analytics_service.get_dashboard_stats()
            
            # Assert
            assert result is not None
            assert result["total_vehicles"] == 100
            assert result["available_vehicles"] == 60
            assert result["in_use_vehicles"] == 30
            assert result["maintenance_vehicles"] == 8
            assert result["out_of_service_vehicles"] == 2
            assert result["total_drivers"] == 80
            assert result["active_drivers"] == 75
            assert result["inactive_drivers"] == 5
            assert result["utilization_rate"] == 0.75
            assert result["fuel_efficiency_avg"] == 12.5
            assert result["maintenance_rate"] == 0.08
            assert result["driver_performance_avg"] == 87.5
            assert result["license_expiry_warnings"] == 3
    
    @pytest.mark.asyncio
    async def test_cross_service_integration(self):
        """Test integration between multiple services"""
        # Arrange
        with patch('services.vehicle_service.db_manager') as mock_vehicle_db, \
             patch('services.driver_service.db_manager') as mock_driver_db, \
             patch('services.analytics_service.VehicleRepository') as mock_vehicle_repo, \
             patch('services.analytics_service.DriverRepository') as mock_driver_repo, \
             patch('services.vehicle_service.event_publisher') as mock_event_publisher:
            
            # Setup vehicle service
            mock_vehicle_db.db = MagicMock()
            mock_vehicle_collection = AsyncMock()
            mock_vehicle_db.db.__getitem__ = MagicMock(return_value=mock_vehicle_collection)
            
            # Setup driver service
            mock_driver_db.db = MagicMock()
            mock_driver_collection = AsyncMock()
            mock_driver_db.db.__getitem__ = MagicMock(return_value=mock_driver_collection)
            
            # Setup analytics service
            mock_vehicle_repo.return_value = AsyncMock()
            mock_driver_repo.return_value = AsyncMock()
            
            # Create service instances
            vehicle_service = VehicleService()
            driver_service = DriverService()
            analytics_service = AnalyticsService()
            
            # Test data
            vehicle_data = {
                "registration_number": "CROSS-001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "fuel_type": "petrol",
                "status": "available"
            }
            
            driver_data = {
                "employee_id": "CROSS-EMP001",
                "first_name": "Cross",
                "last_name": "Integration",
                "email": "cross.integration@company.com",
                "phone": "+1234567890",
                "license_number": "CROSS-LIC001",
                "license_class": "C",
                "license_expiry": datetime(2025, 12, 31),
                "hire_date": datetime(2023, 1, 15),
                "status": "active"
            }
            
            # Mock database responses
            vehicle_id = ObjectId()
            driver_id = ObjectId()
            
            mock_vehicle_collection.insert_one.return_value.inserted_id = vehicle_id
            mock_vehicle_collection.find_one.return_value = {
                "_id": vehicle_id,
                **vehicle_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            mock_driver_collection.insert_one.return_value.inserted_id = driver_id
            mock_driver_collection.find_one.return_value = {
                "_id": driver_id,
                **driver_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Mock analytics responses
            mock_vehicle_repo.return_value.count.return_value = 1
            mock_vehicle_repo.return_value.count_by_status.return_value = {
                "available": 1
            }
            mock_driver_repo.return_value.count.return_value = 1
            mock_driver_repo.return_value.count_by_status.return_value = {
                "active": 1
            }
            
            # Mock additional metrics
            mock_vehicle_repo.return_value.get_utilization_rate.return_value = 0.0
            mock_vehicle_repo.return_value.get_fuel_efficiency_avg.return_value = 0.0
            mock_vehicle_repo.return_value.get_maintenance_rate.return_value = 0.0
            mock_driver_repo.return_value.get_average_performance_score.return_value = 0.0
            mock_driver_repo.return_value.get_license_expiry_warnings.return_value = 0
            
            # Act
            
            # 1. Create vehicle and driver
            created_vehicle = await vehicle_service.create_vehicle(vehicle_data)
            created_driver = await driver_service.create_driver(driver_data)
            
            assert created_vehicle is not None
            assert created_driver is not None
            
            # 2. Get analytics after creation
            stats = await analytics_service.get_dashboard_stats()
            
            assert stats is not None
            assert stats["total_vehicles"] == 1
            assert stats["available_vehicles"] == 1
            assert stats["total_drivers"] == 1
            assert stats["active_drivers"] == 1
            
            # 3. Update vehicle status
            mock_vehicle_collection.find_one.return_value = {
                "_id": vehicle_id,
                **vehicle_data,
                "status": "in_use",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            updated_vehicle = await vehicle_service.update_vehicle(str(vehicle_id), {"status": "in_use"})
            assert updated_vehicle is not None
            
            # 4. Verify events were published
            mock_event_publisher.publish_vehicle_created.assert_called_once()
            mock_event_publisher.publish_vehicle_updated.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across service integration"""
        # Arrange
        with patch('services.vehicle_service.db_manager') as mock_db_manager:
            
            # Mock database to raise error
            mock_db = MagicMock()
            mock_collection = AsyncMock()
            mock_db_manager.db = mock_db
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            # Mock database error
            mock_collection.insert_one.side_effect = Exception("Database connection failed")
            
            vehicle_service = VehicleService()
            
            vehicle_data = {
                "registration_number": "ERROR-001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "fuel_type": "petrol",
                "status": "available"
            }
            
            # Act & Assert
            with pytest.raises(Exception, match="Database connection failed"):
                await vehicle_service.create_vehicle(vehicle_data)
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self):
        """Test concurrent operations integration"""
        # Arrange
        with patch('services.vehicle_service.db_manager') as mock_db_manager, \
             patch('services.vehicle_service.event_publisher') as mock_event_publisher:
            
            # Mock database
            mock_db = MagicMock()
            mock_collection = AsyncMock()
            mock_db_manager.db = mock_db
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            vehicle_service = VehicleService()
            
            # Test data for concurrent operations
            vehicle_data_1 = {
                "registration_number": "CONC-001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "fuel_type": "petrol",
                "status": "available"
            }
            
            vehicle_data_2 = {
                "registration_number": "CONC-002",
                "make": "Honda",
                "model": "Civic",
                "year": 2023,
                "fuel_type": "petrol",
                "status": "available"
            }
            
            # Mock database responses
            vehicle_id_1 = ObjectId()
            vehicle_id_2 = ObjectId()
            
            mock_collection.insert_one.side_effect = [
                MagicMock(inserted_id=vehicle_id_1),
                MagicMock(inserted_id=vehicle_id_2)
            ]
            
            mock_collection.find_one.side_effect = [
                {
                    "_id": vehicle_id_1,
                    **vehicle_data_1,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "_id": vehicle_id_2,
                    **vehicle_data_2,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            # Act - Create vehicles concurrently
            import asyncio
            results = await asyncio.gather(
                vehicle_service.create_vehicle(vehicle_data_1),
                vehicle_service.create_vehicle(vehicle_data_2)
            )
            
            # Assert
            assert len(results) == 2
            assert results[0] is not None
            assert results[1] is not None
            assert results[0]["registration_number"] == "CONC-001"
            assert results[1]["registration_number"] == "CONC-002"
            
            # Verify events were published for both
            assert mock_event_publisher.publish_vehicle_created.call_count == 2
    
    @pytest.mark.asyncio
    async def test_service_lifecycle_integration(self):
        """Test complete service lifecycle integration"""
        # Arrange
        with patch('services.vehicle_service.db_manager') as mock_db_manager, \
             patch('services.vehicle_service.event_publisher') as mock_event_publisher:
            
            # Mock database
            mock_db = MagicMock()
            mock_collection = AsyncMock()
            mock_db_manager.db = mock_db
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            vehicle_service = VehicleService()
            
            # Test data
            vehicle_data = {
                "registration_number": "LIFE-001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "fuel_type": "petrol",
                "status": "available"
            }
            
            vehicle_id = ObjectId()
            
            # Mock database responses for lifecycle
            mock_collection.insert_one.return_value.inserted_id = vehicle_id
            
            # Mock responses for each lifecycle stage
            available_vehicle = {
                "_id": vehicle_id,
                **vehicle_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            in_use_vehicle = {
                **available_vehicle,
                "status": "in_use",
                "updated_at": datetime.utcnow()
            }
            
            maintenance_vehicle = {
                **available_vehicle,
                "status": "maintenance",
                "updated_at": datetime.utcnow()
            }
            
            mock_collection.find_one.side_effect = [
                available_vehicle,  # After creation
                available_vehicle,  # Before first update
                in_use_vehicle,     # After first update
                in_use_vehicle,     # Before second update
                maintenance_vehicle # After second update
            ]
            
            mock_collection.update_one.return_value.modified_count = 1
            mock_collection.delete_one.return_value.deleted_count = 1
            
            # Act - Complete lifecycle
            
            # 1. Create
            created = await vehicle_service.create_vehicle(vehicle_data)
            assert created is not None
            assert created["status"] == "available"
            
            # 2. Update to in_use
            updated_1 = await vehicle_service.update_vehicle(str(vehicle_id), {"status": "in_use"})
            assert updated_1 is not None
            assert updated_1["status"] == "in_use"
            
            # 3. Update to maintenance
            updated_2 = await vehicle_service.update_vehicle(str(vehicle_id), {"status": "maintenance"})
            assert updated_2 is not None
            assert updated_2["status"] == "maintenance"
            
            # 4. Delete
            deleted = await vehicle_service.delete_vehicle(str(vehicle_id))
            assert deleted is True
            
            # Assert - Verify all events were published
            mock_event_publisher.publish_vehicle_created.assert_called_once()
            assert mock_event_publisher.publish_vehicle_updated.call_count == 2
            mock_event_publisher.publish_vehicle_deleted.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_data_consistency_integration(self):
        """Test data consistency across service operations"""
        # Arrange
        with patch('services.vehicle_service.db_manager') as mock_vehicle_db, \
             patch('services.analytics_service.VehicleRepository') as mock_vehicle_repo, \
             patch('services.vehicle_service.event_publisher') as mock_event_publisher:
            
            # Mock vehicle service database
            mock_vehicle_db.db = MagicMock()
            mock_vehicle_collection = AsyncMock()
            mock_vehicle_db.db.__getitem__ = MagicMock(return_value=mock_vehicle_collection)
            
            # Mock analytics repository
            mock_vehicle_repo.return_value = AsyncMock()
            
            vehicle_service = VehicleService()
            analytics_service = AnalyticsService()
            
            # Test data
            vehicle_data = {
                "registration_number": "CONS-001",
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "fuel_type": "petrol",
                "status": "available"
            }
            
            vehicle_id = ObjectId()
            
            # Mock consistent responses
            vehicle_record = {
                "_id": vehicle_id,
                **vehicle_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            mock_vehicle_collection.insert_one.return_value.inserted_id = vehicle_id
            mock_vehicle_collection.find_one.return_value = vehicle_record
            
            # Mock analytics to reflect the same data
            mock_vehicle_repo.return_value.count.return_value = 1
            mock_vehicle_repo.return_value.count_by_status.return_value = {
                "available": 1
            }
            
            # Mock additional metrics
            mock_vehicle_repo.return_value.get_utilization_rate.return_value = 0.0
            mock_vehicle_repo.return_value.get_fuel_efficiency_avg.return_value = 0.0
            mock_vehicle_repo.return_value.get_maintenance_rate.return_value = 0.0
            
            # Act
            
            # 1. Create vehicle
            created = await vehicle_service.create_vehicle(vehicle_data)
            assert created is not None
            assert created["registration_number"] == "CONS-001"
            
            # 2. Get analytics - should reflect the created vehicle
            stats = await analytics_service.get_dashboard_stats()
            assert stats is not None
            assert stats["total_vehicles"] == 1
            assert stats["available_vehicles"] == 1
            
            # 3. Update vehicle status
            updated_vehicle = {
                **vehicle_record,
                "status": "in_use",
                "updated_at": datetime.utcnow()
            }
            
            mock_vehicle_collection.find_one.return_value = updated_vehicle
            mock_vehicle_collection.update_one.return_value.modified_count = 1
            
            # Update analytics to reflect the change
            mock_vehicle_repo.return_value.count_by_status.return_value = {
                "in_use": 1
            }
            
            updated = await vehicle_service.update_vehicle(str(vehicle_id), {"status": "in_use"})
            assert updated is not None
            assert updated["status"] == "in_use"
            
            # 4. Get updated analytics
            stats = await analytics_service.get_dashboard_stats()
            assert stats is not None
            assert stats["total_vehicles"] == 1
            assert stats.get("available_vehicles", 0) == 0
            assert stats.get("in_use_vehicles", 0) == 1
            
            # Assert - Data consistency maintained
            mock_event_publisher.publish_vehicle_created.assert_called_once()
            mock_event_publisher.publish_vehicle_updated.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
class TestVehicleServiceIntegration:
    """Integration tests for Vehicle Service with database"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager"""
        db_manager = AsyncMock(spec=DatabaseManager)
        db_manager.db = MagicMock()
        
        # Mock collection
        mock_collection = AsyncMock()
        db_manager.db.__getitem__ = MagicMock(return_value=mock_collection)
        
        return db_manager, mock_collection
    
    @pytest.fixture
    def mock_event_publisher(self):
        """Mock event publisher"""
        return AsyncMock(spec=EventPublisher)
    
    @pytest.fixture
    def vehicle_service(self, mock_db_manager, mock_event_publisher):
        """Create VehicleService with mocked dependencies"""
        db_manager, mock_collection = mock_db_manager
        
        with patch('services.vehicle_service.db_manager', db_manager), \
             patch('services.vehicle_service.event_publisher', mock_event_publisher):
            service = VehicleService()
            service.collection = mock_collection
            return service, mock_collection, mock_event_publisher
    
    async def test_create_vehicle_integration(self, vehicle_service):
        """Test creating a vehicle with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = vehicle_service
        
        vehicle_data = {
            "registration_number": "ABC-123",
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "fuel_type": "petrol",
            "status": "available",
            "department": "operations"
        }
        
        created_vehicle_id = ObjectId()
        mock_collection.insert_one.return_value.inserted_id = created_vehicle_id
        mock_collection.find_one.return_value = {
            "_id": created_vehicle_id,
            **vehicle_data,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Act
        result = await service.create_vehicle(vehicle_data)
        
        # Assert
        assert result is not None
        assert result["_id"] == str(created_vehicle_id)
        assert result["registration_number"] == "ABC-123"
        assert result["make"] == "Toyota"
        
        # Verify database interactions
        mock_collection.insert_one.assert_called_once()
        mock_collection.find_one.assert_called_once()
        
        # Verify event publication
        mock_event_publisher.publish_vehicle_created.assert_called_once()
    
    async def test_get_vehicle_by_id_integration(self, vehicle_service):
        """Test getting a vehicle by ID with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = vehicle_service
        
        vehicle_id = str(ObjectId())
        vehicle_data = {
            "_id": ObjectId(vehicle_id),
            "registration_number": "ABC-123",
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "fuel_type": "petrol",
            "status": "available",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        mock_collection.find_one.return_value = vehicle_data
        
        # Act
        result = await service.get_vehicle_by_id(vehicle_id)
        
        # Assert
        assert result is not None
        assert result["_id"] == vehicle_id
        assert result["registration_number"] == "ABC-123"
        
        # Verify database interactions
        mock_collection.find_one.assert_called_once_with({"_id": ObjectId(vehicle_id)})
    
    async def test_update_vehicle_integration(self, vehicle_service):
        """Test updating a vehicle with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = vehicle_service
        
        vehicle_id = str(ObjectId())
        update_data = {
            "status": "maintenance",
            "notes": "Routine maintenance"
        }
        
        # Mock update result
        mock_collection.update_one.return_value.modified_count = 1
        
        # Mock the updated vehicle
        updated_vehicle = {
            "_id": ObjectId(vehicle_id),
            "registration_number": "ABC-123",
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "fuel_type": "petrol",
            "status": "maintenance",
            "notes": "Routine maintenance",
            "updated_at": datetime.now(timezone.utc)
        }
        
        mock_collection.find_one.return_value = updated_vehicle
        
        # Act
        result = await service.update_vehicle(vehicle_id, update_data)
        
        # Assert
        assert result is not None
        assert result["_id"] == vehicle_id
        assert result["status"] == "maintenance"
        assert result["notes"] == "Routine maintenance"
        
        # Verify database interactions
        mock_collection.update_one.assert_called_once()
        mock_collection.find_one.assert_called_once()
        
        # Verify event publication
        mock_event_publisher.publish_vehicle_updated.assert_called_once()
    
    async def test_delete_vehicle_integration(self, vehicle_service):
        """Test deleting a vehicle with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = vehicle_service
        
        vehicle_id = str(ObjectId())
        
        # Mock delete result
        mock_collection.delete_one.return_value.deleted_count = 1
        
        # Act
        result = await service.delete_vehicle(vehicle_id)
        
        # Assert
        assert result is True
        
        # Verify database interactions
        mock_collection.delete_one.assert_called_once_with({"_id": ObjectId(vehicle_id)})
        
        # Verify event publication
        mock_event_publisher.publish_vehicle_deleted.assert_called_once()
    
    async def test_get_vehicles_with_pagination_integration(self, vehicle_service):
        """Test getting vehicles with pagination"""
        # Arrange
        service, mock_collection, mock_event_publisher = vehicle_service
        
        vehicles_data = [
            {
                "_id": ObjectId(),
                "registration_number": "ABC-123",
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "fuel_type": "petrol",
                "status": "available"
            },
            {
                "_id": ObjectId(),
                "registration_number": "DEF-456",
                "make": "Honda",
                "model": "Civic",
                "year": 2022,
                "fuel_type": "petrol",
                "status": "in_use"
            }
        ]
        
        # Mock cursor for find operation
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        
        # Mock async iteration
        mock_cursor.__aiter__.return_value = iter(vehicles_data)
        mock_collection.find.return_value = mock_cursor
        
        # Mock count
        mock_collection.count_documents.return_value = 2
        
        # Act
        result = await service.get_vehicles(skip=0, limit=10)
        
        # Assert
        assert result is not None
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "has_more" in result
        
        # Verify database interactions
        mock_collection.find.assert_called_once()
        mock_collection.count_documents.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
class TestDriverServiceIntegration:
    """Integration tests for Driver Service with database"""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager"""
        db_manager = AsyncMock(spec=DatabaseManager)
        db_manager.db = MagicMock()
        
        # Mock collection
        mock_collection = AsyncMock()
        db_manager.db.__getitem__ = MagicMock(return_value=mock_collection)
        
        return db_manager, mock_collection
    
    @pytest.fixture
    def mock_event_publisher(self):
        """Mock event publisher"""
        return AsyncMock(spec=EventPublisher)
    
    @pytest.fixture
    def driver_service(self, mock_db_manager, mock_event_publisher):
        """Create DriverService with mocked dependencies"""
        db_manager, mock_collection = mock_db_manager
        
        with patch('services.driver_service.db_manager', db_manager), \
             patch('services.driver_service.event_publisher', mock_event_publisher):
            service = DriverService()
            service.collection = mock_collection
            return service, mock_collection, mock_event_publisher
    
    async def test_create_driver_integration(self, driver_service):
        """Test creating a driver with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = driver_service
        
        driver_data = {
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "phone": "+1234567890",
            "license_number": "LIC123456",
            "license_class": "C",
            "license_expiry": datetime(2025, 12, 31),
            "hire_date": datetime(2023, 1, 15),
            "department": "operations",
            "status": "active"
        }
        
        created_driver_id = ObjectId()
        mock_collection.insert_one.return_value.inserted_id = created_driver_id
        mock_collection.find_one.return_value = {
            "_id": created_driver_id,
            **driver_data,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Act
        result = await service.create_driver(driver_data)
        
        # Assert
        assert result is not None
        assert result["_id"] == str(created_driver_id)
        assert result["employee_id"] == "EMP001"
        assert result["first_name"] == "John"
        
        # Verify database interactions
        mock_collection.insert_one.assert_called_once()
        mock_collection.find_one.assert_called_once()
        
        # Verify event publication
        mock_event_publisher.publish_driver_created.assert_called_once()
    
    async def test_get_driver_by_id_integration(self, driver_service):
        """Test getting a driver by ID with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = driver_service
        
        driver_id = str(ObjectId())
        driver_data = {
            "_id": ObjectId(driver_id),
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        mock_collection.find_one.return_value = driver_data
        
        # Act
        result = await service.get_driver_by_id(driver_id)
        
        # Assert
        assert result is not None
        assert result["_id"] == driver_id
        assert result["employee_id"] == "EMP001"
        
        # Verify database interactions
        mock_collection.find_one.assert_called_once_with({"_id": ObjectId(driver_id)})
    
    async def test_update_driver_integration(self, driver_service):
        """Test updating a driver with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = driver_service
        
        driver_id = str(ObjectId())
        update_data = {
            "status": "inactive",
            "notes": "Driver on leave"
        }
        
        # Mock update result
        mock_collection.update_one.return_value.modified_count = 1
        
        # Mock the updated driver
        updated_driver = {
            "_id": ObjectId(driver_id),
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "status": "inactive",
            "notes": "Driver on leave",
            "updated_at": datetime.now(timezone.utc)
        }
        
        mock_collection.find_one.return_value = updated_driver
        
        # Act
        result = await service.update_driver(driver_id, update_data)
        
        # Assert
        assert result is not None
        assert result["_id"] == driver_id
        assert result["status"] == "inactive"
        assert result["notes"] == "Driver on leave"
        
        # Verify database interactions
        mock_collection.update_one.assert_called_once()
        mock_collection.find_one.assert_called_once()
        
        # Verify event publication
        mock_event_publisher.publish_driver_updated.assert_called_once()
    
    async def test_delete_driver_integration(self, driver_service):
        """Test deleting a driver with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = driver_service
        
        driver_id = str(ObjectId())
        
        # Mock delete result
        mock_collection.delete_one.return_value.deleted_count = 1
        
        # Act
        result = await service.delete_driver(driver_id)
        
        # Assert
        assert result is True
        
        # Verify database interactions
        mock_collection.delete_one.assert_called_once_with({"_id": ObjectId(driver_id)})
        
        # Verify event publication
        mock_event_publisher.publish_driver_deleted.assert_called_once()
    
    async def test_search_drivers_integration(self, driver_service):
        """Test searching drivers with database integration"""
        # Arrange
        service, mock_collection, mock_event_publisher = driver_service
        
        search_query = "John"
        drivers_data = [
            {
                "_id": ObjectId(),
                "employee_id": "EMP001",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@company.com",
                "status": "active"
            },
            {
                "_id": ObjectId(),
                "employee_id": "EMP002",
                "first_name": "Johnny",
                "last_name": "Smith",
                "email": "johnny.smith@company.com",
                "status": "active"
            }
        ]
        
        # Mock cursor for find operation
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        
        # Mock async iteration
        mock_cursor.__aiter__.return_value = iter(drivers_data)
        mock_collection.find.return_value = mock_cursor
        
        # Mock count
        mock_collection.count_documents.return_value = 2
        
        # Act
        result = await service.search_drivers(search_query)
        
        # Assert
        assert result is not None
        assert "items" in result
        assert "total" in result
        assert len(result["items"]) == 2
        
        # Verify database interactions
        mock_collection.find.assert_called_once()
        mock_collection.count_documents.assert_called_once()
        
        # Verify search query was constructed correctly
        find_call_args = mock_collection.find.call_args[0][0]
        assert "$or" in find_call_args
        assert "$regex" in str(find_call_args)


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    @pytest.fixture
    def mock_motor_client(self):
        """Mock Motor client"""
        import motor.motor_asyncio
        
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock database and collection
            mock_db = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=mock_db)
            mock_client.admin.command = AsyncMock(return_value={"ok": 1})
            
            yield mock_client, mock_db
    
    async def test_database_connection_integration(self, mock_motor_client):
        """Test database connection with proper setup"""
        # Arrange
        mock_client, mock_db = mock_motor_client
        
        # Act
        db_manager = DatabaseManager()
        await db_manager.connect()
        
        # Assert
        assert db_manager._client is not None
        assert db_manager._db is not None
        
        # Verify ping was called
        mock_client.admin.command.assert_called_with('ping')
    
    async def test_database_health_check_integration(self, mock_motor_client):
        """Test database health check"""
        # Arrange
        mock_client, mock_db = mock_motor_client
        
        db_manager = DatabaseManager()
        await db_manager.connect()
        
        # Act
        health_status = await db_manager.health_check()
        
        # Assert
        assert health_status is not None
        assert health_status["status"] == "healthy"
        assert health_status["database_connected"] is True
        assert "response_time_ms" in health_status
    
    async def test_database_disconnection_integration(self, mock_motor_client):
        """Test database disconnection"""
        # Arrange
        mock_client, mock_db = mock_motor_client
        
        db_manager = DatabaseManager()
        await db_manager.connect()
        
        # Act
        await db_manager.disconnect()
        
        # Assert
        assert db_manager._client is None
        assert db_manager._db is None
        
        # Verify close was called
        mock_client.close.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
class TestEventPublisherIntegration:
    """Integration tests for event publishing"""
    
    @pytest.fixture
    def mock_rabbitmq_connection(self):
        """Mock RabbitMQ connection"""
        import aio_pika
        
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connection = AsyncMock()
            mock_channel = AsyncMock()
            mock_exchange = AsyncMock()
            
            mock_connect.return_value = mock_connection
            mock_connection.channel.return_value = mock_channel
            mock_channel.declare_exchange.return_value = mock_exchange
            
            yield mock_connection, mock_channel, mock_exchange
    
    async def test_event_publishing_integration(self, mock_rabbitmq_connection):
        """Test event publishing with RabbitMQ integration"""
        # Arrange
        mock_connection, mock_channel, mock_exchange = mock_rabbitmq_connection
        
        event_publisher = EventPublisher()
        
        vehicle_data = {
            "_id": str(ObjectId()),
            "registration_number": "ABC-123",
            "make": "Toyota",
            "model": "Camry",
            "status": "available"
        }
        
        # Act
        await event_publisher.publish_vehicle_created(vehicle_data)
        
        # Assert
        # Verify connection was established
        mock_connection.channel.assert_called_once()
        mock_channel.declare_exchange.assert_called_once()
        
        # Verify message was published
        mock_exchange.publish.assert_called_once()
        
        # Verify message content
        published_message = mock_exchange.publish.call_args[0][0]
        assert published_message is not None
    
    async def test_event_publishing_with_retry_integration(self, mock_rabbitmq_connection):
        """Test event publishing with retry logic"""
        # Arrange
        mock_connection, mock_channel, mock_exchange = mock_rabbitmq_connection
        
        # Mock first publish to fail, second to succeed
        mock_exchange.publish.side_effect = [
            Exception("Connection failed"),
            None  # Success
        ]
        
        event_publisher = EventPublisher()
        
        vehicle_data = {
            "_id": str(ObjectId()),
            "registration_number": "ABC-123",
            "make": "Toyota",
            "model": "Camry",
            "status": "available"
        }
        
        # Act
        await event_publisher.publish_vehicle_created(vehicle_data)
        
        # Assert
        # Verify publish was called twice (initial attempt + retry)
        assert mock_exchange.publish.call_count == 2
    
    async def test_batch_event_publishing_integration(self, mock_rabbitmq_connection):
        """Test batch event publishing"""
        # Arrange
        mock_connection, mock_channel, mock_exchange = mock_rabbitmq_connection
        
        event_publisher = EventPublisher()
        
        events_data = [
            {
                "event_type": "vehicle_created",
                "data": {
                    "_id": str(ObjectId()),
                    "registration_number": "ABC-123",
                    "make": "Toyota"
                }
            },
            {
                "event_type": "vehicle_updated",
                "data": {
                    "_id": str(ObjectId()),
                    "registration_number": "DEF-456",
                    "status": "maintenance"
                }
            }
        ]
        
        # Act
        await event_publisher.publish_batch_events(events_data)
        
        # Assert
        # Verify connection was established
        mock_connection.channel.assert_called_once()
        mock_channel.declare_exchange.assert_called_once()
        
        # Verify multiple messages were published
        assert mock_exchange.publish.call_count == 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestEndToEndScenarios:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def mock_all_dependencies(self):
        """Mock all external dependencies"""
        # Mock database
        with patch('repositories.database.db_manager') as mock_db_manager, \
             patch('events.publisher.event_publisher') as mock_event_publisher:
            
            # Setup database mock
            mock_db = MagicMock()
            mock_collection = AsyncMock()
            mock_db_manager.db = mock_db
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            
            # Setup event publisher mock
            mock_event_publisher.publish_vehicle_created = AsyncMock()
            mock_event_publisher.publish_vehicle_updated = AsyncMock()
            mock_event_publisher.publish_vehicle_deleted = AsyncMock()
            
            yield mock_db_manager, mock_collection, mock_event_publisher
    
    async def test_full_vehicle_lifecycle_integration(self, mock_all_dependencies):
        """Test complete vehicle lifecycle: create, read, update, delete"""
        # Arrange
        mock_db_manager, mock_collection, mock_event_publisher = mock_all_dependencies
        
        vehicle_service = VehicleService()
        vehicle_service.collection = mock_collection
        
        vehicle_data = {
            "registration_number": "ABC-123",
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "fuel_type": "petrol",
            "status": "available"
        }
        
        vehicle_id = ObjectId()
        
        # Mock create operation
        mock_collection.insert_one.return_value.inserted_id = vehicle_id
        mock_collection.find_one.side_effect = [
            # First call for create
            {
                "_id": vehicle_id,
                **vehicle_data,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            # Second call for read
            {
                "_id": vehicle_id,
                **vehicle_data,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            # Third call for update
            {
                "_id": vehicle_id,
                **vehicle_data,
                "status": "maintenance",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        # Mock update operation
        mock_collection.update_one.return_value.modified_count = 1
        
        # Mock delete operation
        mock_collection.delete_one.return_value.deleted_count = 1
        
        # Act & Assert
        
        # 1. Create vehicle
        created_vehicle = await vehicle_service.create_vehicle(vehicle_data)
        assert created_vehicle is not None
        assert created_vehicle["registration_number"] == "ABC-123"
        mock_event_publisher.publish_vehicle_created.assert_called_once()
        
        # 2. Read vehicle
        read_vehicle = await vehicle_service.get_vehicle_by_id(str(vehicle_id))
        assert read_vehicle is not None
        assert read_vehicle["registration_number"] == "ABC-123"
        
        # 3. Update vehicle
        update_data = {"status": "maintenance"}
        updated_vehicle = await vehicle_service.update_vehicle(str(vehicle_id), update_data)
        assert updated_vehicle is not None
        assert updated_vehicle["status"] == "maintenance"
        mock_event_publisher.publish_vehicle_updated.assert_called_once()
        
        # 4. Delete vehicle
        delete_result = await vehicle_service.delete_vehicle(str(vehicle_id))
        assert delete_result is True
        mock_event_publisher.publish_vehicle_deleted.assert_called_once()
        
        # Verify all database operations were called
        mock_collection.insert_one.assert_called_once()
        assert mock_collection.find_one.call_count == 3
        mock_collection.update_one.assert_called_once()
        mock_collection.delete_one.assert_called_once()
    
    async def test_driver_assignment_workflow_integration(self, mock_all_dependencies):
        """Test driver assignment workflow"""
        # Arrange
        mock_db_manager, mock_collection, mock_event_publisher = mock_all_dependencies
        
        driver_service = DriverService()
        driver_service.collection = mock_collection
        
        driver_data = {
            "employee_id": "EMP001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@company.com",
            "license_number": "LIC123456",
            "license_class": "C",
            "license_expiry": datetime(2025, 12, 31),
            "hire_date": datetime(2023, 1, 15),
            "status": "active"
        }
        
        driver_id = ObjectId()
        
        # Mock create operation
        mock_collection.insert_one.return_value.inserted_id = driver_id
        mock_collection.find_one.return_value = {
            "_id": driver_id,
            **driver_data,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Mock search operation
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.__aiter__.return_value = iter([{
            "_id": driver_id,
            **driver_data
        }])
        
        mock_collection.find.return_value = mock_cursor
        mock_collection.count_documents.return_value = 1
        
        # Act & Assert
        
        # 1. Create driver
        created_driver = await driver_service.create_driver(driver_data)
        assert created_driver is not None
        assert created_driver["employee_id"] == "EMP001"
        
        # 2. Search for available drivers
        search_result = await driver_service.search_drivers("John")
        assert search_result is not None
        assert search_result["total"] == 1
        assert len(search_result["items"]) == 1
        
        # 3. Get driver details
        driver_details = await driver_service.get_driver_by_id(str(driver_id))
        assert driver_details is not None
        assert driver_details["employee_id"] == "EMP001"
        
        # Verify database operations
        mock_collection.insert_one.assert_called_once()
        mock_collection.find_one.assert_called()
        mock_collection.find.assert_called_once()
        mock_collection.count_documents.assert_called_once()
