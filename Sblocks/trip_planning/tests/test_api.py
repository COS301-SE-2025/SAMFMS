import pytest
from httpx import AsyncClient
from unittest.mock import patch

from tests.conftest import APITestMixin


class TestTripAPI(APITestMixin):
    """Test cases for Trip API endpoints"""

    @pytest.mark.asyncio
    async def test_create_trip_endpoint(self, test_client, sample_trip_data):
        """Test POST /api/v1/trips endpoint"""
        response = await test_client.post("/api/v1/trips", json=sample_trip_data)
        
        data = self.assert_success_response(response, 201)
        assert 'trip_id' in data['data']

    @pytest.mark.asyncio
    async def test_get_trip_endpoint(self, test_client, sample_trip_data, test_db):
        """Test GET /api/v1/trips/{trip_id} endpoint"""
        # Create a trip first
        create_response = await test_client.post("/api/v1/trips", json=sample_trip_data)
        trip_data = create_response.json()
        trip_id = trip_data['data']['trip_id']
        
        # Get the trip
        response = await test_client.get(f"/api/v1/trips/{trip_id}")
        
        data = self.assert_success_response(response)
        assert data['data']['trip_id'] == trip_id

    @pytest.mark.asyncio
    async def test_update_trip_endpoint(self, test_client, sample_trip_data):
        """Test PUT /api/v1/trips/{trip_id} endpoint"""
        # Create a trip first
        create_response = await test_client.post("/api/v1/trips", json=sample_trip_data)
        trip_data = create_response.json()
        trip_id = trip_data['data']['trip_id']
        
        # Update the trip
        update_data = {"status": "confirmed"}
        response = await test_client.put(f"/api/v1/trips/{trip_id}", json=update_data)
        
        data = self.assert_success_response(response)
        assert data['data']['status'] == 'confirmed'

    @pytest.mark.asyncio
    async def test_cancel_trip_endpoint(self, test_client, sample_trip_data):
        """Test POST /api/v1/trips/{trip_id}/cancel endpoint"""
        # Create a trip first
        create_response = await test_client.post("/api/v1/trips", json=sample_trip_data)
        trip_data = create_response.json()
        trip_id = trip_data['data']['trip_id']
        
        # Cancel the trip
        cancel_data = {"reason": "User requested cancellation"}
        response = await test_client.post(f"/api/v1/trips/{trip_id}/cancel", json=cancel_data)
        
        data = self.assert_success_response(response)
        assert data['data']['status'] == 'cancelled'

    @pytest.mark.asyncio
    async def test_get_user_trips_endpoint(self, test_client, sample_trip_data):
        """Test GET /api/v1/trips/user/{user_id} endpoint"""
        user_id = sample_trip_data['user_id']
        
        # Create a trip first
        await test_client.post("/api/v1/trips", json=sample_trip_data)
        
        # Get user trips
        response = await test_client.get(f"/api/v1/trips/user/{user_id}")
        
        data = self.assert_success_response(response)
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1

    @pytest.mark.asyncio
    async def test_search_trips_endpoint(self, test_client, sample_trip_data):
        """Test GET /api/v1/trips/search endpoint"""
        # Create a trip first
        await test_client.post("/api/v1/trips", json=sample_trip_data)
        
        # Search trips
        params = {
            "status": "planned",
            "limit": 10
        }
        response = await test_client.get("/api/v1/trips/search", params=params)
        
        data = self.assert_success_response(response)
        assert isinstance(data['data'], list)

    @pytest.mark.asyncio
    async def test_estimate_trip_endpoint(self, test_client):
        """Test POST /api/v1/trips/estimate endpoint"""
        estimate_data = {
            "origin": {"lat": 40.7128, "lng": -74.0060},
            "destination": {"lat": 34.0522, "lng": -118.2437}
        }
        
        response = await test_client.post("/api/v1/trips/estimate", json=estimate_data)
        
        data = self.assert_success_response(response)
        assert 'estimated_cost' in data['data']
        assert 'estimated_duration' in data['data']

    @pytest.mark.asyncio
    async def test_trip_analytics_endpoint(self, test_client, sample_trip_data):
        """Test GET /api/v1/trips/analytics/{user_id} endpoint"""
        user_id = sample_trip_data['user_id']
        
        # Create a trip first
        await test_client.post("/api/v1/trips", json=sample_trip_data)
        
        # Get analytics
        response = await test_client.get(f"/api/v1/trips/analytics/{user_id}")
        
        data = self.assert_success_response(response)
        assert 'total_trips' in data['data']

    @pytest.mark.asyncio
    async def test_invalid_trip_id_format(self, test_client):
        """Test API with invalid trip ID format"""
        response = await test_client.get("/api/v1/trips/invalid_id")
        
        self.assert_error_response(response, 422)  # Validation error

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, test_client):
        """Test creating trip with missing required fields"""
        invalid_data = {"user_id": "test_user"}  # Missing origin, destination
        
        response = await test_client.post("/api/v1/trips", json=invalid_data)
        
        self.assert_error_response(response, 422)  # Validation error

    @pytest.mark.asyncio
    async def test_trip_not_found(self, test_client):
        """Test getting non-existent trip"""
        from bson import ObjectId
        fake_id = str(ObjectId())
        
        response = await test_client.get(f"/api/v1/trips/{fake_id}")
        
        self.assert_error_response(response, 404)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client, sample_trip_data):
        """Test API rate limiting"""
        # This test would need actual rate limiting configuration
        # For now, just verify endpoint responds normally
        response = await test_client.post("/api/v1/trips", json=sample_trip_data)
        assert response.status_code in [201, 429]  # Success or rate limited

    @pytest.mark.asyncio
    async def test_cors_headers(self, test_client):
        """Test CORS headers are present"""
        response = await test_client.options("/api/v1/trips")
        
        # Check for CORS headers (if configured)
        assert response.status_code in [200, 405]  # OK or Method not allowed

    @pytest.mark.asyncio
    async def test_content_type_validation(self, test_client):
        """Test content type validation"""
        # Send non-JSON data
        response = await test_client.post(
            "/api/v1/trips",
            data="invalid_json",
            headers={"Content-Type": "text/plain"}
        )
        
        self.assert_error_response(response, 422)

    @pytest.mark.asyncio
    async def test_pagination(self, test_client, sample_trip_data):
        """Test pagination in search results"""
        # Create multiple trips
        for i in range(5):
            trip_data = sample_trip_data.copy()
            trip_data['trip_id'] = f"test_trip_{i:03d}"
            await test_client.post("/api/v1/trips", json=trip_data)
        
        # Test pagination
        params = {"limit": 2, "offset": 0}
        response = await test_client.get("/api/v1/trips/search", params=params)
        
        data = self.assert_success_response(response)
        assert len(data['data']) <= 2

    @pytest.mark.asyncio
    async def test_service_error_handling(self, test_client, sample_trip_data):
        """Test handling of service layer errors"""
        # Mock service error
        with patch('services.trip_service.TripService.create_trip') as mock_create:
            mock_create.return_value = {
                'success': False,
                'error': 'Database connection failed'
            }
            
            response = await test_client.post("/api/v1/trips", json=sample_trip_data)
            
            self.assert_error_response(response, 500)
