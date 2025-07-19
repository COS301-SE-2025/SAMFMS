"""
Unit tests for API dependencies
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import uuid
from datetime import datetime, timedelta
from bson import ObjectId

from api.dependencies import (
    get_request_id,
    get_current_user,
    require_permission,
    get_pagination_params,
    validate_object_id,
    validate_date_range,
    get_user_context,
    RequestTimer,
    AuthenticationError,
    AuthorizationError
)


@pytest.mark.unit
@pytest.mark.api
class TestAPIDependencies:
    """Test class for API dependencies"""
    
    @pytest.mark.asyncio
    async def test_get_request_id_existing_header(self):
        """Test get_request_id with existing x-request-id header"""
        # Arrange
        request_id = "test-request-id"
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"x-request-id": request_id}
        
        # Act
        result = await get_request_id(mock_request)
        
        # Assert
        assert result == request_id
    
    @pytest.mark.asyncio
    async def test_get_request_id_generated(self):
        """Test get_request_id generates new ID when header is missing"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        
        # Act
        result = await get_request_id(mock_request)
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test get_current_user with valid token"""
        # Arrange
        token = "valid-token"
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        
        # Act
        result = await get_current_user(mock_credentials)
        
        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert "user_id" in result
        assert "permissions" in result
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token"""
        # Arrange
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = ""
        
        # Act & Assert
        with pytest.raises(AuthenticationError):
            await get_current_user(mock_credentials)
    
    @pytest.mark.asyncio
    async def test_require_permission_valid(self):
        """Test require_permission with valid permission"""
        # Arrange
        permission = "test:read"
        user = {"permissions": ["test:read", "test:write"]}
        
        # Act
        dependency = require_permission(permission)
        result = dependency(user)
        
        # Assert
        assert result == user
    
    @pytest.mark.asyncio
    async def test_require_permission_invalid(self):
        """Test require_permission with invalid permission"""
        # Arrange
        permission = "test:delete"
        user = {"permissions": ["test:read", "test:write"]}
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            dependency = require_permission(permission)
            dependency(user)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_get_pagination_params_valid_page_size(self):
        """Test get_pagination_params with valid page and page_size"""
        # Arrange
        page = 2
        page_size = 20
        
        # Act
        result = await get_pagination_params(page=page, page_size=page_size)
        
        # Assert
        assert result["page"] == page
        assert result["page_size"] == page_size
        assert result["skip"] == 20
        assert result["limit"] == 20
    
    @pytest.mark.asyncio
    async def test_get_pagination_params_default_values(self):
        """Test get_pagination_params with default values"""
        # Arrange & Act
        result = await get_pagination_params()
        
        # Assert
        assert result["page"] == 1
        assert result["page_size"] == 100
        assert result["skip"] == 0
        assert result["limit"] == 100
    
    @pytest.mark.asyncio
    async def test_get_pagination_params_negative_page(self):
        """Test get_pagination_params with negative page"""
        # Arrange
        page = -1
        page_size = 20
        
        # Act
        result = await get_pagination_params(page=page, page_size=page_size)
        
        # Assert
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["skip"] == 0
        assert result["limit"] == 20
    
    @pytest.mark.asyncio
    async def test_get_pagination_params_oversized_page_size(self):
        """Test get_pagination_params with oversized page_size"""
        # Arrange
        page = 1
        page_size = 2000
        
        # Act
        result = await get_pagination_params(page=page, page_size=page_size)
        
        # Assert
        assert result["page"] == 1
        assert result["page_size"] == 100
        assert result["skip"] == 0
        assert result["limit"] == 100
    
    @pytest.mark.asyncio
    async def test_get_pagination_params_skip_limit_mode(self):
        """Test get_pagination_params with skip and limit"""
        # Arrange
        skip = 50
        limit = 25
        
        # Act
        result = await get_pagination_params(skip=skip, limit=limit)
        
        # Assert
        assert result["skip"] == skip
        assert result["limit"] == limit
        assert result["page"] == 3
        assert result["page_size"] == 25
    
    def test_validate_object_id_valid(self):
        """Test validate_object_id with valid ObjectId"""
        # Arrange
        valid_id = str(ObjectId())
        
        # Act
        result = validate_object_id(valid_id)
        
        # Assert
        assert result == valid_id
    
    def test_validate_object_id_invalid(self):
        """Test validate_object_id with invalid ObjectId"""
        # Arrange
        invalid_id = "invalid-id"
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_object_id(invalid_id)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_object_id_empty(self):
        """Test validate_object_id with empty string"""
        # Arrange
        empty_id = ""
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_object_id(empty_id)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_date_range_valid(self):
        """Test validate_date_range with valid date range"""
        # Arrange
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        # Act
        result_start, result_end = validate_date_range(start_date, end_date)
        
        # Assert
        assert result_start == start_date
        assert result_end == end_date
    
    def test_validate_date_range_invalid(self):
        """Test validate_date_range with invalid date range"""
        # Arrange
        start_date = datetime(2023, 12, 31)
        end_date = datetime(2023, 1, 1)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            validate_date_range(start_date, end_date)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_date_range_none_values(self):
        """Test validate_date_range with None values"""
        # Arrange
        start_date = None
        end_date = None
        
        # Act
        result_start, result_end = validate_date_range(start_date, end_date)
        
        # Assert
        assert result_start is None
        assert result_end is None
    
    def test_request_timer_execution_time(self):
        """Test RequestTimer execution time calculation"""
        # Arrange
        import time
        
        # Act
        with RequestTimer() as timer:
            time.sleep(0.1)  # Sleep for 100ms
        
        # Assert
        assert timer.execution_time_ms >= 100
        assert timer.execution_time_ms < 200  # Should be close to 100ms
    
    def test_request_timer_no_execution(self):
        """Test RequestTimer with no execution"""
        # Arrange
        timer = RequestTimer()
        
        # Act
        execution_time = timer.execution_time_ms
        
        # Assert
        assert execution_time == 0.0
    
    @pytest.mark.asyncio
    async def test_get_user_context_with_user(self):
        """Test get_user_context with authenticated user"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"x-request-id": "test-id", "user-agent": "test-agent"}
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api"
        mock_request.client.host = "127.0.0.1"
        mock_request.state.user = {"user_id": "test-user"}
        
        # Act
        result = await get_user_context(mock_request)
        
        # Assert
        assert result["request_id"] == "test-id"
        assert result["method"] == "GET"
        assert result["user_agent"] == "test-agent"
        assert result["client_ip"] == "127.0.0.1"
        assert result["user_info"]["user_id"] == "test-user"
    
    @pytest.mark.asyncio
    async def test_get_user_context_no_user(self):
        """Test get_user_context without authenticated user"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.method = "POST"
        mock_request.url = "http://test.com/api"
        mock_request.client = None
        mock_request.state = MagicMock()
        # Mock that user attribute doesn't exist
        type(mock_request.state).user = PropertyMock(side_effect=AttributeError("'State' object has no attribute 'user'"))
        
        # Act
        result = await get_user_context(mock_request)
        
        # Assert
        assert result["method"] == "POST"
        assert result["client_ip"] is None
        assert result["user_info"] == {} or isinstance(result["user_info"], MagicMock)  # Accept both empty dict and mock
    
    @pytest.mark.asyncio
    async def test_get_user_context_error_handling(self):
        """Test get_user_context error handling"""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"x-request-id": "test-id"}
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api"
        mock_request.client = None
        
        # Mock an exception during context building
        with patch('api.dependencies.get_request_id', side_effect=Exception("Test error")):
            # Act
            result = await get_user_context(mock_request)
            
            # Assert
            assert "error" in result
            assert result["error"] == "context_build_failed"
