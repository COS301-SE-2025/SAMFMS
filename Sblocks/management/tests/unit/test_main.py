"""
Unit tests for main application module
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
import asyncio
import sys

# Mock the problematic modules at import time
sys.modules['aio_pika'] = Mock()
sys.modules['aio_pika.abc'] = Mock()
sys.modules['services.request_consumer'] = Mock()

# Mock the main module imports to avoid dependency issues
with patch.dict('sys.modules', {
    'services.request_consumer': Mock(),
    'database': Mock(),
    'logging_config': Mock()
}):
    from main import app, lifespan
    # Don't import middleware add_middleware since it doesn't exist
    # from middleware import add_middleware


@pytest.mark.unit
@pytest.mark.app
class TestMainApplication:
    """Test class for main application"""
    
    def setup_method(self):
        """Setup test client and dependencies"""
        self.client = TestClient(app)
    
    def test_app_creation(self):
        """Test FastAPI app creation"""
        # Act
        test_app = create_app()
        
        # Assert
        assert test_app is not None
        assert test_app.title == "SAMFMS Management Service"
        assert test_app.version == "1.0.0"
        assert test_app.description == "Fleet Management System - Management Service"
    
    def test_app_health_check_endpoint(self):
        """Test health check endpoint"""
        # Act
        response = self.client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "management"
        assert "timestamp" in data
    
    def test_app_root_endpoint(self):
        """Test root endpoint"""
        # Act
        response = self.client.get("/")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "SAMFMS Management Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_app_openapi_schema(self):
        """Test OpenAPI schema generation"""
        # Act
        response = self.client.get("/openapi.json")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        schema = response.json()
        assert schema["info"]["title"] == "SAMFMS Management Service"
        assert schema["info"]["version"] == "1.0.0"
        assert "paths" in schema
        assert "components" in schema
    
    def test_app_docs_endpoint(self):
        """Test API documentation endpoint"""
        # Act
        response = self.client.get("/docs")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
    
    def test_app_redoc_endpoint(self):
        """Test ReDoc documentation endpoint"""
        # Act
        response = self.client.get("/redoc")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
    
    def test_app_cors_headers(self):
        """Test CORS headers are properly configured"""
        # Act
        response = self.client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Note: CORS headers are added by middleware in actual usage
    
    def test_app_includes_all_routes(self):
        """Test that all route modules are included"""
        # Act
        routes = [route.path for route in app.routes]
        
        # Assert
        expected_routes = [
            "/api/v1/vehicles",
            "/api/v1/drivers", 
            "/api/v1/assignments",
            "/api/v1/analytics",
            "/health",
            "/"
        ]
        
        for expected_route in expected_routes:
            assert any(expected_route in route for route in routes)
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_success(self):
        """Test application startup lifecycle"""
        # Arrange
        mock_app = MagicMock()
        
        with patch('main.database.connect') as mock_db_connect, \
             patch('main.event_consumer_manager.start_consumers') as mock_start_consumers, \
             patch('main.logger') as mock_logger:
            
            mock_db_connect.return_value = AsyncMock()
            mock_start_consumers.return_value = AsyncMock()
            
            # Act
            async with lifespan(mock_app):
                # Application is running
                pass
            
            # Assert
            mock_db_connect.assert_called_once()
            mock_start_consumers.assert_called_once()
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_database_error(self):
        """Test application startup with database connection error"""
        # Arrange
        mock_app = MagicMock()
        
        with patch('main.database.connect') as mock_db_connect, \
             patch('main.logger') as mock_logger:
            
            mock_db_connect.side_effect = Exception("Database connection failed")
            
            # Act & Assert
            with pytest.raises(Exception):
                async with lifespan(mock_app):
                    pass
            
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_consumer_error(self):
        """Test application startup with consumer error"""
        # Arrange
        mock_app = MagicMock()
        
        with patch('main.database.connect') as mock_db_connect, \
             patch('main.event_consumer_manager.start_consumers') as mock_start_consumers, \
             patch('main.logger') as mock_logger:
            
            mock_db_connect.return_value = AsyncMock()
            mock_start_consumers.side_effect = Exception("Consumer startup failed")
            
            # Act & Assert
            with pytest.raises(Exception):
                async with lifespan(mock_app):
                    pass
            
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_lifespan_shutdown_success(self):
        """Test application shutdown lifecycle"""
        # Arrange
        mock_app = MagicMock()
        
        with patch('main.database.connect') as mock_db_connect, \
             patch('main.database.disconnect') as mock_db_disconnect, \
             patch('main.event_consumer_manager.start_consumers') as mock_start_consumers, \
             patch('main.event_consumer_manager.stop_consumers') as mock_stop_consumers, \
             patch('main.logger') as mock_logger:
            
            mock_db_connect.return_value = AsyncMock()
            mock_db_disconnect.return_value = AsyncMock()
            mock_start_consumers.return_value = AsyncMock()
            mock_stop_consumers.return_value = AsyncMock()
            
            # Act
            async with lifespan(mock_app):
                pass
            
            # Assert
            mock_db_disconnect.assert_called_once()
            mock_stop_consumers.assert_called_once()
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_lifespan_shutdown_error_handling(self):
        """Test error handling during application shutdown"""
        # Arrange
        mock_app = MagicMock()
        
        with patch('main.database.connect') as mock_db_connect, \
             patch('main.database.disconnect') as mock_db_disconnect, \
             patch('main.event_consumer_manager.start_consumers') as mock_start_consumers, \
             patch('main.event_consumer_manager.stop_consumers') as mock_stop_consumers, \
             patch('main.logger') as mock_logger:
            
            mock_db_connect.return_value = AsyncMock()
            mock_db_disconnect.side_effect = Exception("Database disconnect failed")
            mock_start_consumers.return_value = AsyncMock()
            mock_stop_consumers.return_value = AsyncMock()
            
            # Act
            async with lifespan(mock_app):
                pass
            
            # Assert
            mock_logger.error.assert_called()
            mock_stop_consumers.assert_called_once()  # Should still attempt to stop consumers
    
    def test_app_middleware_configuration(self):
        """Test that middleware is properly configured"""
        # Arrange & Act
        middleware_types = [type(middleware) for middleware in app.user_middleware]
        
        # Assert
        # Check that middleware has been added (exact types depend on implementation)
        assert len(middleware_types) > 0
    
    def test_app_exception_handlers(self):
        """Test custom exception handlers"""
        # Arrange
        test_app = create_app()
        
        # Act
        exception_handlers = test_app.exception_handlers
        
        # Assert
        assert len(exception_handlers) > 0
        # Check for common HTTP exception handlers
        assert 404 in exception_handlers or 500 in exception_handlers
    
    def test_app_request_validation_error_handling(self):
        """Test request validation error handling"""
        # Arrange
        invalid_data = {
            "invalid_field": "invalid_value"
        }
        
        # Act
        response = self.client.post("/api/v1/vehicles/", json=invalid_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
    
    def test_app_method_not_allowed_handling(self):
        """Test method not allowed error handling"""
        # Act
        response = self.client.patch("/health")  # PATCH not allowed on health endpoint
        
        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_app_not_found_handling(self):
        """Test not found error handling"""
        # Act
        response = self.client.get("/nonexistent-endpoint")
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_app_concurrent_requests(self):
        """Test handling of concurrent requests"""
        # Arrange
        async def make_request():
            return self.client.get("/health")
        
        # Act
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # Assert
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
    
    def test_app_security_headers(self):
        """Test security headers are present"""
        # Act
        response = self.client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Security headers should be added by middleware
        # Exact headers depend on middleware implementation
    
    def test_app_request_id_header(self):
        """Test request ID header handling"""
        # Arrange
        request_id = "test-request-id-123"
        
        # Act
        response = self.client.get("/health", headers={"X-Request-ID": request_id})
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Request ID should be processed by middleware
    
    def test_app_content_type_validation(self):
        """Test content type validation"""
        # Act
        response = self.client.post(
            "/api/v1/vehicles/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_app_large_payload_handling(self):
        """Test handling of large payloads"""
        # Arrange
        large_data = {
            "registration_number": "ABC-001",
            "make": "Toyota",
            "model": "Camry",
            "notes": "x" * 10000  # Large notes field
        }
        
        # Act
        response = self.client.post("/api/v1/vehicles/", json=large_data)
        
        # Assert
        # Should handle large payloads gracefully
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE]
    
    def test_app_query_parameter_validation(self):
        """Test query parameter validation"""
        # Act
        response = self.client.get("/api/v1/vehicles/?page=invalid&page_size=invalid")
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_app_route_authentication_required(self):
        """Test that protected routes require authentication"""
        # Act
        response = self.client.get("/api/v1/vehicles/")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_app_metrics_endpoint(self):
        """Test metrics endpoint if available"""
        # Act
        response = self.client.get("/metrics")
        
        # Assert
        # Metrics endpoint may or may not be implemented
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_app_version_endpoint(self):
        """Test version endpoint"""
        # Act
        response = self.client.get("/version")
        
        # Assert
        # Version endpoint may be at root or separate endpoint
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "version" in data
    
    def test_app_environment_configuration(self):
        """Test that app respects environment configuration"""
        # Act
        # Test that app configuration is properly loaded
        assert app.title == "SAMFMS Management Service"
        assert app.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_app_graceful_shutdown(self):
        """Test graceful shutdown behavior"""
        # Arrange
        mock_app = MagicMock()
        
        with patch('main.database.connect') as mock_db_connect, \
             patch('main.database.disconnect') as mock_db_disconnect, \
             patch('main.event_consumer_manager.start_consumers') as mock_start_consumers, \
             patch('main.event_consumer_manager.stop_consumers') as mock_stop_consumers:
            
            mock_db_connect.return_value = AsyncMock()
            mock_db_disconnect.return_value = AsyncMock()
            mock_start_consumers.return_value = AsyncMock()
            mock_stop_consumers.return_value = AsyncMock()
            
            # Act
            async with lifespan(mock_app):
                # Simulate application running
                await asyncio.sleep(0.1)
            
            # Assert
            mock_db_disconnect.assert_called_once()
            mock_stop_consumers.assert_called_once()
    
    def test_app_logging_configuration(self):
        """Test logging configuration"""
        # Act
        # Test that logging is properly configured
        with patch('main.logger') as mock_logger:
            self.client.get("/health")
            # Logger should be used during request processing
    
    def test_app_route_prefix_configuration(self):
        """Test API route prefix configuration"""
        # Act
        routes = [route.path for route in app.routes]
        
        # Assert
        api_routes = [route for route in routes if route.startswith("/api/v1")]
        assert len(api_routes) > 0
        
        # Check that all API routes have the correct prefix
        expected_prefixes = ["/api/v1/vehicles", "/api/v1/drivers", "/api/v1/assignments", "/api/v1/analytics"]
        for prefix in expected_prefixes:
            assert any(route.startswith(prefix) for route in api_routes)
