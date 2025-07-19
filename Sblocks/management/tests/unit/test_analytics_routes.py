"""
Unit tests for analytics routes
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, status
from datetime import datetime, timezone
from bson import ObjectId
import httpx

from api.routes.analytics import router
from schemas.responses import StandardResponse

# Create a test app instance
app = FastAPI()
app.include_router(router)

# Use httpx AsyncClient instead of TestClient
async def make_request(method, url, **kwargs):
    """Helper to make HTTP requests"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        return await client.request(method, url, **kwargs)


@pytest.mark.unit
@pytest.mark.api
class TestAnalyticsRoutes:
    """Test class for analytics API routes"""
    
    def setup_method(self):
        """Setup test client and dependencies"""
        self.base_url = "/api/v1/analytics"
        
        # Mock authentication
        self.mock_user = {
            "user_id": "test_user",
            "role": "manager",
            "permissions": ["analytics:read"],
            "department": "operations"
        }
        
    @pytest.mark.asyncio
    async def test_get_dashboard_stats_success(self):
        """Test getting dashboard statistics successfully"""
        # Arrange
        mock_stats = {
            "total_vehicles": 25,
            "available_vehicles": 20,
            "active_drivers": 15,
            "total_assignments": 100,
            "fleet_utilization": 80.0,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_dashboard_stats.return_value = mock_stats
            
            # Act
            response = self.client.get(f"{self.base_url}/dashboard")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_vehicles"] == 25
            assert data["data"]["available_vehicles"] == 20
            assert data["data"]["fleet_utilization"] == 80.0
            mock_service.get_dashboard_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_dashboard_stats_permission_denied(self):
        """Test dashboard stats access denied for insufficient permissions"""
        # Arrange
        unauthorized_user = {
            "user_id": "test_user",
            "role": "driver",
            "permissions": ["drivers:read"],
            "department": "operations"
        }
        
        with patch('api.routes.analytics.get_current_user') as mock_auth:
            mock_auth.return_value = unauthorized_user
            
            # Act
            response = self.client.get(f"{self.base_url}/dashboard")
            
            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_get_fleet_utilization_success(self):
        """Test getting fleet utilization successfully"""
        # Arrange
        mock_utilization = {
            "total_vehicles": 25,
            "in_use": 15,
            "available": 10,
            "maintenance": 0,
            "utilization_rate": 60.0,
            "period": "daily",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_fleet_utilization.return_value = mock_utilization
            
            # Act
            response = self.client.get(f"{self.base_url}/fleet-utilization")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["utilization_rate"] == 60.0
            assert data["data"]["total_vehicles"] == 25
            mock_service.get_fleet_utilization.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_fleet_utilization_with_period(self):
        """Test getting fleet utilization with specific period"""
        # Arrange
        mock_utilization = {
            "total_vehicles": 25,
            "in_use": 12,
            "available": 13,
            "maintenance": 0,
            "utilization_rate": 48.0,
            "period": "weekly",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_fleet_utilization.return_value = mock_utilization
            
            # Act
            response = self.client.get(f"{self.base_url}/fleet-utilization?period=weekly")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["period"] == "weekly"
            assert data["data"]["utilization_rate"] == 48.0
            mock_service.get_fleet_utilization.assert_called_once_with("weekly")
    
    @pytest.mark.asyncio
    async def test_get_vehicle_usage_success(self):
        """Test getting vehicle usage statistics successfully"""
        # Arrange
        mock_usage = {
            "total_trips": 150,
            "total_distance": 5000.0,
            "total_fuel_consumed": 800.0,
            "average_trip_distance": 33.33,
            "most_used_vehicles": [
                {"vehicle_id": "vehicle_1", "registration": "ABC-001", "usage_count": 25},
                {"vehicle_id": "vehicle_2", "registration": "ABC-002", "usage_count": 20}
            ],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicle_usage.return_value = mock_usage
            
            # Act
            response = self.client.get(f"{self.base_url}/vehicle-usage")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_trips"] == 150
            assert data["data"]["total_distance"] == 5000.0
            assert len(data["data"]["most_used_vehicles"]) == 2
            mock_service.get_vehicle_usage.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_vehicle_usage_with_date_range(self):
        """Test getting vehicle usage with date range"""
        # Arrange
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        mock_usage = {
            "total_trips": 50,
            "total_distance": 1500.0,
            "period": f"{start_date} to {end_date}",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_vehicle_usage.return_value = mock_usage
            
            # Act
            response = self.client.get(
                f"{self.base_url}/vehicle-usage?start_date={start_date}&end_date={end_date}"
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_trips"] == 50
            mock_service.get_vehicle_usage.assert_called_once_with(
                start_date=start_date, 
                end_date=end_date
            )
    
    @pytest.mark.asyncio
    async def test_get_assignment_metrics_success(self):
        """Test getting assignment metrics successfully"""
        # Arrange
        mock_metrics = {
            "total_assignments": 100,
            "active_assignments": 15,
            "completed_assignments": 80,
            "cancelled_assignments": 5,
            "assignment_completion_rate": 80.0,
            "average_assignment_duration": 4.5,
            "top_drivers": [
                {"driver_id": "driver_1", "name": "John Doe", "assignment_count": 12},
                {"driver_id": "driver_2", "name": "Jane Smith", "assignment_count": 10}
            ],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignment_metrics.return_value = mock_metrics
            
            # Act
            response = self.client.get(f"{self.base_url}/assignment-metrics")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_assignments"] == 100
            assert data["data"]["assignment_completion_rate"] == 80.0
            assert len(data["data"]["top_drivers"]) == 2
            mock_service.get_assignment_metrics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_assignment_metrics_with_department(self):
        """Test getting assignment metrics filtered by department"""
        # Arrange
        department = "operations"
        mock_metrics = {
            "total_assignments": 60,
            "active_assignments": 8,
            "completed_assignments": 50,
            "cancelled_assignments": 2,
            "assignment_completion_rate": 83.3,
            "department": department,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_assignment_metrics.return_value = mock_metrics
            
            # Act
            response = self.client.get(f"{self.base_url}/assignment-metrics?department={department}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["department"] == department
            assert data["data"]["assignment_completion_rate"] == 83.3
            mock_service.get_assignment_metrics.assert_called_once_with(department=department)
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self):
        """Test error handling when service raises exceptions"""
        # Arrange
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_dashboard_stats.side_effect = Exception("Database connection failed")
            
            # Act
            response = self.client.get(f"{self.base_url}/dashboard")
            
            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    @pytest.mark.asyncio
    async def test_invalid_date_range_validation(self):
        """Test validation of invalid date ranges"""
        # Arrange
        invalid_start = "2024-13-01"  # Invalid month
        invalid_end = "2024-01-32"    # Invalid day
        
        with patch('api.routes.analytics.get_current_user') as mock_auth:
            mock_auth.return_value = self.mock_user
            
            # Act
            response = self.client.get(
                f"{self.base_url}/vehicle-usage?start_date={invalid_start}&end_date={invalid_end}"
            )
            
            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_analytics_endpoints_require_authentication(self):
        """Test that analytics endpoints require authentication"""
        # Arrange - No authentication provided
        
        # Act & Assert
        endpoints = [
            f"{self.base_url}/dashboard",
            f"{self.base_url}/fleet-utilization",
            f"{self.base_url}/vehicle-usage",
            f"{self.base_url}/assignment-metrics"
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_analytics_performance_metrics(self):
        """Test that analytics endpoints include performance metrics"""
        # Arrange
        mock_stats = {
            "total_vehicles": 25,
            "processing_time": 0.15,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        with patch('api.routes.analytics.analytics_service') as mock_service, \
             patch('api.routes.analytics.get_current_user') as mock_auth:
            
            # Mock dependencies
            mock_auth.return_value = self.mock_user
            mock_service.get_dashboard_stats.return_value = mock_stats
            
            # Act
            response = self.client.get(f"{self.base_url}/dashboard")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "processing_time" in data["data"] or "generated_at" in data["data"]
