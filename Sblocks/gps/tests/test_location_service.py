"""
Test location service
"""
import pytest
from datetime import datetime
from services.location_service import LocationService


class TestLocationService:
    """Test cases for LocationService"""
    
    @pytest.mark.asyncio
    async def test_update_vehicle_location(self, test_db, sample_vehicle_location):
        """Test updating vehicle location"""
        location_service = LocationService()
        location_service.db = test_db
        
        # Update location
        result = await location_service.update_vehicle_location(
            **sample_vehicle_location
        )
        
        assert result is not None
        assert result.vehicle_id == sample_vehicle_location["vehicle_id"]
        assert result.latitude == sample_vehicle_location["latitude"]
        assert result.longitude == sample_vehicle_location["longitude"]
    
    @pytest.mark.asyncio
    async def test_get_vehicle_location(self, test_db, sample_vehicle_location):
        """Test getting vehicle location"""
        location_service = LocationService()
        location_service.db = test_db
        
        # First update location
        await location_service.update_vehicle_location(**sample_vehicle_location)
        
        # Then retrieve it
        result = await location_service.get_vehicle_location(
            sample_vehicle_location["vehicle_id"]
        )
        
        assert result is not None
        assert result.vehicle_id == sample_vehicle_location["vehicle_id"]
    
    @pytest.mark.asyncio
    async def test_get_location_history(self, test_db, sample_vehicle_location):
        """Test getting location history"""
        location_service = LocationService()
        location_service.db = test_db
        
        # Update location multiple times
        for i in range(3):
            location_data = sample_vehicle_location.copy()
            location_data["latitude"] += i * 0.001
            await location_service.update_vehicle_location(**location_data)
        
        # Get history
        history = await location_service.get_location_history(
            sample_vehicle_location["vehicle_id"]
        )
        
        assert len(history) == 3
        assert all(h.vehicle_id == sample_vehicle_location["vehicle_id"] for h in history)
    
    @pytest.mark.asyncio
    async def test_start_tracking_session(self, test_db):
        """Test starting tracking session"""
        location_service = LocationService()
        location_service.db = test_db
        
        session = await location_service.start_tracking_session(
            vehicle_id="test_vehicle",
            user_id="test_user"
        )
        
        assert session is not None
        assert session.vehicle_id == "test_vehicle"
        assert session.user_id == "test_user"
        assert session.is_active is True
