import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from bson import ObjectId

from services.trip_service import TripService
from tests.conftest import DatabaseTestMixin


class TestTripService(DatabaseTestMixin):
    """Test cases for TripService"""

    @pytest.fixture
    async def trip_service(self, test_db, mock_rabbitmq_publisher):
        """Create TripService instance for testing"""
        service = TripService()
        service.db = test_db
        service.publisher = mock_rabbitmq_publisher
        return service

    @pytest.mark.asyncio
    async def test_create_trip_success(self, trip_service, sample_trip_data):
        """Test successful trip creation"""
        # Act
        result = await trip_service.create_trip(sample_trip_data)
        
        # Assert
        assert result['success'] is True
        assert 'trip_id' in result['data']
        assert result['data']['status'] == 'planned'
        
        # Verify trip was saved to database
        trip = await trip_service.get_trip(result['data']['trip_id'])
        assert trip['success'] is True
        assert trip['data']['user_id'] == sample_trip_data['user_id']

    @pytest.mark.asyncio
    async def test_create_trip_invalid_data(self, trip_service):
        """Test trip creation with invalid data"""
        invalid_data = {"user_id": "test_user"}  # Missing required fields
        
        result = await trip_service.create_trip(invalid_data)
        
        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_get_trip_existing(self, trip_service, sample_trip_data, test_db):
        """Test retrieving an existing trip"""
        # Arrange
        trip_id = await self.create_test_trip(test_db.db, sample_trip_data)
        
        # Act
        result = await trip_service.get_trip(trip_id)
        
        # Assert
        assert result['success'] is True
        assert result['data']['user_id'] == sample_trip_data['user_id']

    @pytest.mark.asyncio
    async def test_get_trip_not_found(self, trip_service):
        """Test retrieving a non-existent trip"""
        fake_id = str(ObjectId())
        
        result = await trip_service.get_trip(fake_id)
        
        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    @pytest.mark.asyncio
    async def test_update_trip_status(self, trip_service, sample_trip_data, test_db):
        """Test updating trip status"""
        # Arrange
        trip_id = await self.create_test_trip(test_db.db, sample_trip_data)
        
        # Act
        result = await trip_service.update_trip_status(trip_id, 'in_progress')
        
        # Assert
        assert result['success'] is True
        assert result['data']['status'] == 'in_progress'

    @pytest.mark.asyncio
    async def test_get_user_trips(self, trip_service, sample_trip_data, test_db):
        """Test retrieving trips for a specific user"""
        # Arrange
        user_id = sample_trip_data['user_id']
        await self.create_test_trip(test_db.db, sample_trip_data)
        
        # Create another trip for same user
        sample_trip_data['trip_id'] = 'test_trip_002'
        await self.create_test_trip(test_db.db, sample_trip_data)
        
        # Act
        result = await trip_service.get_user_trips(user_id)
        
        # Assert
        assert result['success'] is True
        assert len(result['data']) == 2

    @pytest.mark.asyncio
    async def test_cancel_trip(self, trip_service, sample_trip_data, test_db):
        """Test trip cancellation"""
        # Arrange
        trip_id = await self.create_test_trip(test_db.db, sample_trip_data)
        
        # Act
        result = await trip_service.cancel_trip(trip_id, "User requested cancellation")
        
        # Assert
        assert result['success'] is True
        assert result['data']['status'] == 'cancelled'

    @pytest.mark.asyncio
    async def test_search_trips_by_date_range(self, trip_service, sample_trip_data, test_db):
        """Test searching trips by date range"""
        # Arrange
        sample_trip_data['created_at'] = datetime.utcnow()
        await self.create_test_trip(test_db.db, sample_trip_data)
        
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow() + timedelta(days=1)
        
        # Act
        result = await trip_service.search_trips(
            start_date=start_date,
            end_date=end_date
        )
        
        # Assert
        assert result['success'] is True
        assert len(result['data']) >= 1

    @pytest.mark.asyncio
    async def test_estimate_trip_cost(self, trip_service, sample_trip_data):
        """Test trip cost estimation"""
        # Act
        result = await trip_service.estimate_trip_cost(
            sample_trip_data['origin'],
            sample_trip_data['destination']
        )
        
        # Assert
        assert result['success'] is True
        assert 'estimated_cost' in result['data']
        assert result['data']['estimated_cost'] > 0

    @pytest.mark.asyncio
    async def test_validate_trip_constraints(self, trip_service, sample_trip_data):
        """Test trip constraint validation"""
        # Act
        result = await trip_service.validate_trip_constraints(sample_trip_data)
        
        # Assert
        assert result['success'] is True
        assert result['data']['valid'] is True

    @pytest.mark.asyncio
    async def test_get_trip_analytics(self, trip_service, sample_trip_data, test_db):
        """Test retrieving trip analytics"""
        # Arrange
        user_id = sample_trip_data['user_id']
        await self.create_test_trip(test_db.db, sample_trip_data)
        
        # Act
        result = await trip_service.get_trip_analytics(user_id)
        
        # Assert
        assert result['success'] is True
        assert 'total_trips' in result['data']
        assert 'total_distance' in result['data']

    @pytest.mark.asyncio
    async def test_database_error_handling(self, trip_service):
        """Test handling of database errors"""
        # Mock database error
        with patch.object(trip_service.db.db.trips, 'find_one', side_effect=Exception("Database error")):
            result = await trip_service.get_trip("test_id")
            
            assert result['success'] is False
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_publisher_error_handling(self, trip_service, sample_trip_data, mock_rabbitmq_publisher):
        """Test handling of publisher errors"""
        # Mock publisher error
        mock_rabbitmq_publisher.publish_trip_event.side_effect = Exception("Publisher error")
        
        result = await trip_service.create_trip(sample_trip_data)
        
        # Trip should still be created even if event publishing fails
        assert result['success'] is True
