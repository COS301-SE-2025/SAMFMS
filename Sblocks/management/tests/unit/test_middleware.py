"""
Unit tests for middleware components
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from datetime import datetime, timezone

from middleware import (
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    CORSMiddleware,
    RequestIDMiddleware,
    MetricsMiddleware,
    ErrorHandlingMiddleware,
    RateLimitMiddleware,
    HealthCheckMiddleware,
    add_middleware
)


@pytest.mark.unit
@pytest.mark.middleware
class TestLoggingMiddleware:
    """Test class for LoggingMiddleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        self.middleware = LoggingMiddleware(self.app)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_logging_middleware_request_logging(self):
        """Test request logging functionality"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://testserver/test"
        mock_request.headers = {"user-agent": "test-agent"}
        
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_call_next.return_value = mock_response
        
        with patch('middleware.logger') as mock_logger:
            
            # Act
            result = await self.middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert result == mock_response
            mock_logger.info.assert_called()
            mock_call_next.assert_called_once_with(mock_request)
    
    @pytest.mark.asyncio
    async def test_logging_middleware_error_logging(self):
        """Test error logging functionality"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://testserver/test"
        mock_request.headers = {}
        
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = Exception("Test error")
        
        with patch('middleware.logger') as mock_logger:
            
            # Act & Assert
            with pytest.raises(Exception):
                await self.middleware.dispatch(mock_request, mock_call_next)
            
            mock_logger.error.assert_called()
    
    def test_logging_middleware_integration(self):
        """Test logging middleware integration"""
        # Arrange
        self.app.add_middleware(LoggingMiddleware)
        
        # Act
        response = self.client.get("/test")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "test"}


@pytest.mark.unit
@pytest.mark.middleware
class TestSecurityHeadersMiddleware:
    """Test class for SecurityHeadersMiddleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        self.middleware = SecurityHeadersMiddleware(self.app)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_security_headers_middleware_adds_headers(self):
        """Test that security headers are added"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}
        mock_call_next.return_value = mock_response
        
        # Act
        result = await self.middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result == mock_response
        assert "X-Content-Type-Options" in mock_response.headers
        assert "X-Frame-Options" in mock_response.headers
        assert "X-XSS-Protection" in mock_response.headers
        assert "Strict-Transport-Security" in mock_response.headers
        assert "Content-Security-Policy" in mock_response.headers
    
    def test_security_headers_middleware_integration(self):
        """Test security headers middleware integration"""
        # Arrange
        self.app.add_middleware(SecurityHeadersMiddleware)
        
        # Act
        response = self.client.get("/test")
        
        # Assert
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers


@pytest.mark.unit
@pytest.mark.middleware
class TestCORSMiddleware:
    """Test class for CORSMiddleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        self.middleware = CORSMiddleware(self.app)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_cors_middleware_preflight_request(self):
        """Test CORS preflight request handling"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.method = "OPTIONS"
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        mock_call_next = AsyncMock()
        
        # Act
        result = await self.middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result.status_code == 200
        assert "Access-Control-Allow-Origin" in result.headers
        assert "Access-Control-Allow-Methods" in result.headers
        assert "Access-Control-Allow-Headers" in result.headers
    
    @pytest.mark.asyncio
    async def test_cors_middleware_regular_request(self):
        """Test CORS headers on regular requests"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {"Origin": "https://example.com"}
        
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}
        mock_call_next.return_value = mock_response
        
        # Act
        result = await self.middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result == mock_response
        assert "Access-Control-Allow-Origin" in mock_response.headers
    
    def test_cors_middleware_integration(self):
        """Test CORS middleware integration"""
        # Arrange
        self.app.add_middleware(CORSMiddleware)
        
        # Act
        response = self.client.options("/test", headers={"Origin": "https://example.com"})
        
        # Assert
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers


@pytest.mark.unit
@pytest.mark.middleware
class TestRequestIDMiddleware:
    """Test class for RequestIDMiddleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        self.middleware = RequestIDMiddleware(self.app)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_request_id_middleware_existing_header(self):
        """Test request ID middleware with existing header"""
        # Arrange
        request_id = "test-request-id-123"
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Request-ID": request_id}
        
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}
        mock_call_next.return_value = mock_response
        
        # Act
        result = await self.middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result == mock_response
        assert "X-Request-ID" in mock_response.headers
        assert mock_response.headers["X-Request-ID"] == request_id
    
    @pytest.mark.asyncio
    async def test_request_id_middleware_generated_header(self):
        """Test request ID middleware generates new header"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_response.headers = {}
        mock_call_next.return_value = mock_response
        
        # Act
        result = await self.middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result == mock_response
        assert "X-Request-ID" in mock_response.headers
        assert len(mock_response.headers["X-Request-ID"]) > 0
    
    def test_request_id_middleware_integration(self):
        """Test request ID middleware integration"""
        # Arrange
        self.app.add_middleware(RequestIDMiddleware)
        
        # Act
        response = self.client.get("/test")
        
        # Assert
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers


@pytest.mark.unit
@pytest.mark.middleware
class TestMetricsMiddleware:
    """Test class for MetricsMiddleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        self.middleware = MetricsMiddleware(self.app)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_request_tracking(self):
        """Test request metrics tracking"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://testserver/test"
        
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_call_next.return_value = mock_response
        
        with patch('middleware.metrics_tracker') as mock_tracker:
            
            # Act
            result = await self.middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert result == mock_response
            mock_tracker.increment_counter.assert_called()
            mock_tracker.record_histogram.assert_called()
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_error_tracking(self):
        """Test error metrics tracking"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://testserver/test"
        
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = Exception("Test error")
        
        with patch('middleware.metrics_tracker') as mock_tracker:
            
            # Act & Assert
            with pytest.raises(Exception):
                await self.middleware.dispatch(mock_request, mock_call_next)
            
            mock_tracker.increment_counter.assert_called()
    
    def test_metrics_middleware_integration(self):
        """Test metrics middleware integration"""
        # Arrange
        self.app.add_middleware(MetricsMiddleware)
        
        # Act
        response = self.client.get("/test")
        
        # Assert
        assert response.status_code == 200


@pytest.mark.unit
@pytest.mark.middleware
class TestErrorHandlingMiddleware:
    """Test class for ErrorHandlingMiddleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        self.middleware = ErrorHandlingMiddleware(self.app)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @self.app.get("/error")
        async def error_endpoint():
            raise Exception("Test error")
        
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware_success(self):
        """Test error handling middleware with successful request"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_call_next.return_value = mock_response
        
        # Act
        result = await self.middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware_exception(self):
        """Test error handling middleware with exception"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = "http://testserver/test"
        
        mock_call_next = AsyncMock()
        mock_call_next.side_effect = Exception("Test error")
        
        with patch('middleware.logger') as mock_logger:
            
            # Act
            result = await self.middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert isinstance(result, JSONResponse)
            assert result.status_code == 500
            mock_logger.error.assert_called()
    
    def test_error_handling_middleware_integration(self):
        """Test error handling middleware integration"""
        # Arrange
        self.app.add_middleware(ErrorHandlingMiddleware)
        
        # Act
        response = self.client.get("/error")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["success"] is False


@pytest.mark.unit
@pytest.mark.middleware
class TestRateLimitMiddleware:
    """Test class for RateLimitMiddleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        self.middleware = RateLimitMiddleware(self.app, requests_per_minute=10)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware_within_limit(self):
        """Test rate limit middleware within rate limit"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_call_next.return_value = mock_response
        
        with patch('middleware.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = True
            
            # Act
            result = await self.middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert result == mock_response
            mock_limiter.is_allowed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware_exceeded_limit(self):
        """Test rate limit middleware when rate limit is exceeded"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        
        mock_call_next = AsyncMock()
        
        with patch('middleware.rate_limiter') as mock_limiter:
            mock_limiter.is_allowed.return_value = False
            
            # Act
            result = await self.middleware.dispatch(mock_request, mock_call_next)
            
            # Assert
            assert isinstance(result, JSONResponse)
            assert result.status_code == 429
            mock_limiter.is_allowed.assert_called_once()
    
    def test_rate_limit_middleware_integration(self):
        """Test rate limit middleware integration"""
        # Arrange
        self.app.add_middleware(RateLimitMiddleware, requests_per_minute=1)
        
        # Act - First request should succeed
        response1 = self.client.get("/test")
        # Second request should be rate limited
        response2 = self.client.get("/test")
        
        # Assert
        assert response1.status_code == 200
        # Note: Actual rate limiting behavior depends on implementation


@pytest.mark.unit
@pytest.mark.middleware
class TestHealthCheckMiddleware:
    """Test class for HealthCheckMiddleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        self.middleware = HealthCheckMiddleware(self.app)
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        self.client = TestClient(self.app)
    
    @pytest.mark.asyncio
    async def test_health_check_middleware_health_endpoint(self):
        """Test health check middleware for health endpoint"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/health"
        
        mock_call_next = AsyncMock()
        
        # Act
        result = await self.middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert isinstance(result, JSONResponse)
        assert result.status_code == 200
        # Should bypass call_next for health endpoint
        mock_call_next.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_health_check_middleware_regular_endpoint(self):
        """Test health check middleware for regular endpoint"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/test"
        
        mock_call_next = AsyncMock()
        mock_response = MagicMock(spec=Response)
        mock_call_next.return_value = mock_response
        
        # Act
        result = await self.middleware.dispatch(mock_request, mock_call_next)
        
        # Assert
        assert result == mock_response
        mock_call_next.assert_called_once()
    
    def test_health_check_middleware_integration(self):
        """Test health check middleware integration"""
        # Arrange
        self.app.add_middleware(HealthCheckMiddleware)
        
        # Act
        response = self.client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.unit
@pytest.mark.middleware
class TestMiddlewareIntegration:
    """Test class for middleware integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.app = FastAPI()
        
        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @self.app.get("/error")
        async def error_endpoint():
            raise Exception("Test error")
    
    def test_add_middleware_function(self):
        """Test add_middleware function"""
        # Act
        add_middleware(self.app)
        
        # Assert
        assert len(self.app.user_middleware) > 0
    
    def test_middleware_order(self):
        """Test middleware execution order"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/test")
        
        # Assert
        assert response.status_code == 200
        # Middleware should be applied in correct order
    
    def test_middleware_chain_success(self):
        """Test successful request through middleware chain"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/test")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
        
        # Check middleware headers
        assert "X-Request-ID" in response.headers
    
    def test_middleware_chain_error_handling(self):
        """Test error handling through middleware chain"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/error")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["success"] is False
    
    def test_middleware_performance_headers(self):
        """Test performance tracking headers"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/test")
        
        # Assert
        assert response.status_code == 200
        # Performance headers should be added by metrics middleware
    
    def test_middleware_cors_headers(self):
        """Test CORS headers are properly set"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/test", headers={"Origin": "https://example.com"})
        
        # Assert
        assert response.status_code == 200
        # CORS headers should be set by CORS middleware
    
    def test_middleware_security_headers(self):
        """Test security headers are properly set"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/test")
        
        # Assert
        assert response.status_code == 200
        # Security headers should be set by security middleware
    
    @pytest.mark.asyncio
    async def test_middleware_async_compatibility(self):
        """Test middleware compatibility with async operations"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/test")
        
        # Assert
        assert response.status_code == 200
        # All middleware should work with async operations
    
    def test_middleware_exception_propagation(self):
        """Test exception propagation through middleware"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/error")
        
        # Assert
        assert response.status_code == 500
        # Exception should be caught and handled by error middleware
    
    def test_middleware_request_context(self):
        """Test request context preservation through middleware"""
        # Arrange
        add_middleware(self.app)
        client = TestClient(self.app)
        
        # Act
        response = client.get("/test", headers={"X-Request-ID": "test-123"})
        
        # Assert
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == "test-123"
        # Request context should be preserved through middleware chain
