"""
Comprehensive Test Suite for SAMFMS Core
Tests database, configuration, error handling, authentication, and service discovery
"""

import pytest
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

# Test configuration
@pytest.fixture
def test_config():
    """Test configuration fixture"""
    return {
        "database": {
            "url": "mongodb://localhost:27017",
            "name": "samfms_test",
            "max_pool_size": 10,
            "min_pool_size": 2
        },
        "rabbitmq": {
            "url": "amqp://guest:guest@localhost:5672/",
            "exchange": "samfms_test"
        },
        "redis": {
            "url": "redis://localhost:6379/0"
        },
        "security": {
            "jwt_secret": "test_secret_key_very_long_and_secure",
            "jwt_algorithm": "HS256",
            "access_token_expire_minutes": 15
        }
    }

@pytest.fixture
def mock_env_vars(test_config):
    """Mock environment variables"""
    env_vars = {
        "MONGODB_URL": test_config["database"]["url"],
        "DATABASE_NAME": test_config["database"]["name"],
        "RABBITMQ_URL": test_config["rabbitmq"]["url"],
        "REDIS_URL": test_config["redis"]["url"],
        "JWT_SECRET_KEY": test_config["security"]["jwt_secret"],
        "JWT_ALGORITHM": test_config["security"]["jwt_algorithm"],
        "ENVIRONMENT": "test"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

# Database Tests
class TestDatabaseManager:
    """Test database manager functionality"""
    
    @pytest.fixture
    async def db_manager(self, mock_env_vars):
        """Database manager fixture"""
        from Core.database import DatabaseManager
        manager = DatabaseManager()
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_database_connection(self, db_manager):
        """Test database connection"""
        # Mock the Motor client
        with patch('Core.database.AsyncIOMotorClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            await db_manager.connect()
            
            assert db_manager.is_connected is True
            mock_client.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, db_manager):
        """Test database health check"""
        # Mock successful health check
        with patch('Core.database.AsyncIOMotorClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_db = AsyncMock()
            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.command.return_value = {"ok": 1}
            mock_client.return_value = mock_client_instance
            
            await db_manager.connect()
            health = await db_manager.health_check()
            
            assert health["status"] == "healthy"
            assert health["connected"] is True
    
    @pytest.mark.asyncio
    async def test_database_get_collection(self, db_manager):
        """Test getting database collection"""
        with patch('Core.database.AsyncIOMotorClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            mock_client.return_value = mock_client_instance
            
            await db_manager.connect()
            collection = db_manager.get_collection("test_collection")
            
            assert collection is not None
            mock_db.__getitem__.assert_called_with("test_collection")

# Configuration Tests
class TestConfiguration:
    """Test configuration management"""
    
    @pytest.mark.asyncio
    async def test_config_loading(self, mock_env_vars):
        """Test configuration loading from environment"""
        from Core.config.settings import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        assert config.database.url == mock_env_vars["MONGODB_URL"]
        assert config.database.name == mock_env_vars["DATABASE_NAME"]
        assert config.security.jwt_secret == mock_env_vars["JWT_SECRET_KEY"]
    
    @pytest.mark.asyncio
    async def test_config_validation(self, mock_env_vars):
        """Test configuration validation"""
        from Core.config.settings import ConfigManager
        
        # Test with missing required field
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                ConfigManager()
    
    @pytest.mark.asyncio
    async def test_config_defaults(self, mock_env_vars):
        """Test configuration defaults"""
        from Core.config.settings import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Test default values
        assert config.database.max_pool_size == 50
        assert config.database.min_pool_size == 10
        assert config.security.access_token_expire_minutes == 15

# Error Handling Tests
class TestErrorHandling:
    """Test error handling system"""
    
    @pytest.mark.asyncio
    async def test_samfms_error_creation(self):
        """Test SAMFMS error creation"""
        from Core.common.exceptions import SAMFMSError
        
        error = SAMFMSError("Test error", "TEST_001", {"extra": "data"})
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_001"
        assert error.details == {"extra": "data"}
        assert error.correlation_id is not None
    
    @pytest.mark.asyncio
    async def test_validation_error(self):
        """Test validation error"""
        from Core.common.exceptions import ValidationError
        
        error = ValidationError("Invalid data", field="username")
        
        assert error.message == "Invalid data"
        assert error.field == "username"
        assert "VALIDATION_ERROR" in error.error_code
    
    @pytest.mark.asyncio
    async def test_database_error(self):
        """Test database error"""
        from Core.common.exceptions import DatabaseError
        
        error = DatabaseError("Connection failed", operation="connect")
        
        assert error.message == "Connection failed"
        assert error.operation == "connect"
        assert "DATABASE_ERROR" in error.error_code
    
    @pytest.mark.asyncio
    async def test_correlation_id_middleware(self):
        """Test correlation ID middleware"""
        from Core.common.exceptions import correlation_id_middleware
        from fastapi import Request, Response
        
        # Mock request and response
        request = Mock(spec=Request)
        request.headers = {}
        request.state = Mock()
        
        response = Mock(spec=Response)
        response.headers = {}
        
        # Mock call_next
        async def mock_call_next(req):
            return response
        
        # Test middleware
        result = await correlation_id_middleware(request, mock_call_next)
        
        assert hasattr(request.state, 'correlation_id')
        assert request.state.correlation_id is not None

# Authentication Tests
class TestAuthentication:
    """Test authentication service"""
    
    @pytest.fixture
    def mock_user_data(self):
        """Mock user data"""
        return {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "manager",
            "permissions": ["read:vehicles", "write:vehicles"],
            "organization_id": "org_123",
            "fleet_ids": ["fleet_1", "fleet_2"]
        }
    
    @pytest.mark.asyncio
    async def test_token_verification_success(self, mock_env_vars, mock_user_data):
        """Test successful token verification"""
        from Core.auth_service import AuthService
        from fastapi.security import HTTPAuthorizationCredentials
        
        auth_service = AuthService()
        
        # Mock security service response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_user_data
            mock_post.return_value.__aenter__.return_value = mock_response
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="test_token"
            )
            
            user_data = await auth_service.verify_token(credentials)
            
            assert user_data.user_id == mock_user_data["user_id"]
            assert user_data.email == mock_user_data["email"]
            assert user_data.role.value == mock_user_data["role"]
    
    @pytest.mark.asyncio
    async def test_token_verification_failure(self, mock_env_vars):
        """Test token verification failure"""
        from Core.auth_service import AuthService, AuthenticationError
        from fastapi.security import HTTPAuthorizationCredentials
        
        auth_service = AuthService()
        
        # Mock security service error response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_post.return_value.__aenter__.return_value = mock_response
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="invalid_token"
            )
            
            with pytest.raises(AuthenticationError):
                await auth_service.verify_token(credentials)
    
    @pytest.mark.asyncio
    async def test_permission_checking(self, mock_env_vars):
        """Test permission checking"""
        from Core.auth_service import UserData, UserRole, Permission, PermissionScope
        
        permissions = [
            Permission("read", "vehicles", PermissionScope.FLEET),
            Permission("write", "vehicles", PermissionScope.ORGANIZATION)
        ]
        
        user_data = UserData(
            user_id="test_user",
            email="test@example.com",
            role=UserRole.MANAGER,
            permissions=permissions
        )
        
        # Test permission checking
        assert user_data.has_permission("read:vehicles:fleet") is True
        assert user_data.has_permission("write:vehicles:organization") is True
        assert user_data.has_permission("delete:vehicles:system") is False
    
    @pytest.mark.asyncio
    async def test_admin_permissions(self, mock_env_vars):
        """Test admin permissions (should have all)"""
        from Core.auth_service import UserData, UserRole, Permission
        
        user_data = UserData(
            user_id="admin_user",
            email="admin@example.com",
            role=UserRole.ADMIN,
            permissions=[]  # Admin doesn't need explicit permissions
        )
        
        # Test that admin has all permissions
        assert user_data.has_permission("delete:system:system") is True
        assert user_data.has_permission("read:anything:anywhere") is True
    
    @pytest.mark.asyncio
    async def test_token_caching(self, mock_env_vars, mock_user_data):
        """Test token caching functionality"""
        from Core.auth_service import AuthService
        from fastapi.security import HTTPAuthorizationCredentials
        
        auth_service = AuthService()
        
        # Mock security service response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_user_data
            mock_post.return_value.__aenter__.return_value = mock_response
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="test_token"
            )
            
            # First call should hit the security service
            user_data1 = await auth_service.verify_token(credentials)
            assert mock_post.call_count == 1
            
            # Second call should use cache
            user_data2 = await auth_service.verify_token(credentials)
            assert mock_post.call_count == 1  # Should not increase
            
            assert user_data1.user_id == user_data2.user_id

# Service Discovery Tests
class TestServiceDiscovery:
    """Test service discovery functionality"""
    
    @pytest.mark.asyncio
    async def test_service_registration(self):
        """Test service registration"""
        from Core.common.service_discovery import ServiceDiscovery, ServiceStatus
        
        sd = ServiceDiscovery()
        await sd.start()
        
        try:
            service_info = await sd.register_service(
                name="test_service",
                host="localhost",
                port=8000,
                tags=["test", "api"]
            )
            
            assert service_info.name == "test_service"
            assert service_info.host == "localhost"
            assert service_info.port == 8000
            assert "test" in service_info.tags
            
            # Test discovery
            discovered = await sd.discover_service("test_service")
            assert discovered is not None
            assert discovered.name == "test_service"
        
        finally:
            await sd.stop()
    
    @pytest.mark.asyncio
    async def test_service_health_checking(self):
        """Test service health checking"""
        from Core.common.service_discovery import ServiceDiscovery, ServiceStatus
        
        sd = ServiceDiscovery(health_check_interval=1)  # 1 second for testing
        await sd.start()
        
        try:
            # Register service with health check endpoint
            await sd.register_service(
                name="health_test_service",
                host="localhost",
                port=8001,
                health_check_url="/health"
            )
            
            # Mock health check response
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_get.return_value.__aenter__.return_value = mock_response
                
                # Wait for health check
                await asyncio.sleep(2)
                
                service = await sd.discover_service("health_test_service")
                assert service is not None
        
        finally:
            await sd.stop()
    
    @pytest.mark.asyncio
    async def test_service_client_calls(self):
        """Test service client calls"""
        from Core.common.service_discovery import ServiceDiscovery, ServiceClient
        
        sd = ServiceDiscovery()
        await sd.start()
        
        try:
            # Register a service
            await sd.register_service(
                name="api_service",
                host="localhost",
                port=8002
            )
            
            # Update service status to healthy
            await sd.registry.update_status("api_service", ServiceStatus.HEALTHY)
            await sd.registry.update_heartbeat("api_service")
            
            # Test service call
            with patch('aiohttp.ClientSession.request') as mock_request:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"result": "success"}
                mock_request.return_value.__aenter__.return_value = mock_response
                
                async with sd.get_client() as client:
                    result = await client.call_service(
                        "api_service",
                        "GET",
                        "/test"
                    )
                    
                    assert result["result"] == "success"
        
        finally:
            await sd.stop()

# Integration Tests
class TestIntegration:
    """Integration tests for multiple components"""
    
    @pytest.mark.asyncio
    async def test_database_and_config_integration(self, mock_env_vars):
        """Test database and configuration integration"""
        from Core.database import DatabaseManager
        from Core.config.settings import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Use config in database manager
        with patch('Core.database.AsyncIOMotorClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            db_manager = DatabaseManager()
            await db_manager.connect()
            
            # Verify connection was made with config values
            mock_client.assert_called_once()
            args, kwargs = mock_client.call_args
            assert config.database.url in str(args[0])
    
    @pytest.mark.asyncio
    async def test_error_handling_with_correlation_id(self):
        """Test error handling with correlation ID propagation"""
        from Core.common.exceptions import SAMFMSError, get_correlation_id, set_correlation_id
        
        # Set correlation ID
        correlation_id = "test-correlation-123"
        set_correlation_id(correlation_id)
        
        # Create error
        error = SAMFMSError("Test error")
        
        # Verify correlation ID is included
        assert error.correlation_id == correlation_id
        
        # Test error response
        response = error.to_response()
        assert response["correlation_id"] == correlation_id

# Performance Tests
class TestPerformance:
    """Performance-related tests"""
    
    @pytest.mark.asyncio
    async def test_token_cache_performance(self, mock_env_vars, mock_user_data):
        """Test token cache performance under load"""
        from Core.auth_service import AuthService
        from fastapi.security import HTTPAuthorizationCredentials
        import time
        
        auth_service = AuthService()
        
        # Mock security service response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_user_data
            mock_post.return_value.__aenter__.return_value = mock_response
            
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="perf_test_token"
            )
            
            # Time first call (should hit security service)
            start_time = time.time()
            await auth_service.verify_token(credentials)
            first_call_time = time.time() - start_time
            
            # Time subsequent calls (should use cache)
            start_time = time.time()
            for _ in range(100):
                await auth_service.verify_token(credentials)
            cached_calls_time = time.time() - start_time
            
            # Cache should be significantly faster
            avg_cached_time = cached_calls_time / 100
            assert avg_cached_time < first_call_time / 10  # At least 10x faster
    
    @pytest.mark.asyncio
    async def test_service_discovery_scalability(self):
        """Test service discovery with many services"""
        from Core.common.service_discovery import ServiceDiscovery
        
        sd = ServiceDiscovery()
        await sd.start()
        
        try:
            # Register many services
            num_services = 100
            for i in range(num_services):
                await sd.register_service(
                    name=f"service_{i}",
                    host="localhost",
                    port=8000 + i,
                    tags=[f"tag_{i % 10}"]
                )
            
            # Test discovery performance
            import time
            start_time = time.time()
            
            # Discover all services
            services = await sd.get_healthy_services()
            
            discovery_time = time.time() - start_time
            
            # Should be fast even with many services
            assert discovery_time < 1.0  # Less than 1 second
            assert len(services) <= num_services  # Some might not be healthy
        
        finally:
            await sd.stop()

# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after each test"""
    yield
    
    # Clear any global state
    from Core.auth_service import shutdown_auth_service
    from Core.common.service_discovery import shutdown_service_discovery
    
    try:
        await shutdown_auth_service()
        await shutdown_service_discovery()
    except:
        pass  # Ignore cleanup errors

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
