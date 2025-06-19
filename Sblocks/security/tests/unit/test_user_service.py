"""Unit tests for UserService."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.user_service import UserService
from models.api_models import CreateUserRequest


class TestUserService:
    """Test UserService functionality."""
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, mock_user_repository, test_user_data):
        """Test getting all users."""
        mock_users = [test_user_data, {**test_user_data, "user_id": "user-2", "email": "user2@example.com"}]
        mock_user_repository.get_all_users.return_value = mock_users
        
        with patch('services.user_service.UserRepository', mock_user_repository):
            result = await UserService.get_all_users()
            
            assert len(result) == 2
            assert result[0]["id"] == test_user_data["user_id"]
            mock_user_repository.get_all_users.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, mock_user_repository, test_user_data):
        """Test getting user by ID successfully."""
        mock_user_repository.find_by_id.return_value = test_user_data
        
        with patch('services.user_service.UserRepository', mock_user_repository):
            result = await UserService.get_user_by_id(test_user_data["user_id"])
            
            assert result["user_id"] == test_user_data["user_id"]
            mock_user_repository.find_by_id.assert_called_once_with(test_user_data["user_id"])
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_user_repository):
        """Test getting user by ID when user doesn't exist."""
        mock_user_repository.find_by_id.return_value = None
        
        with patch('services.user_service.UserRepository', mock_user_repository):
            with pytest.raises(ValueError, match="User not found"):
                await UserService.get_user_by_id("nonexistent-user")
    
    @pytest.mark.asyncio
    async def test_create_user_manually_success(self, mock_user_repository, mock_audit_repository):
        """Test manual user creation success."""
        user_data = CreateUserRequest(
            full_name="Test User",
            email="test@example.com",
            role="driver",
            password="TestPassword123!",
            phoneNo="+1234567890"
        )
        
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.create_user.return_value = {"user_id": "new-user-123"}
        
        with patch('services.user_service.UserRepository', mock_user_repository), \
             patch('services.user_service.AuditRepository', mock_audit_repository), \
             patch('services.user_service.get_password_hash', return_value="hashed_password"):
            
            result = await UserService.create_user_manually(user_data, "admin-user-123")
            
            assert result["message"] == "User created successfully"
            mock_user_repository.find_by_email.assert_called_once()
            mock_user_repository.create_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_manually_duplicate_email(self, mock_user_repository):
        """Test manual user creation with duplicate email."""
        user_data = CreateUserRequest(
            full_name="Test User",
            email="test@example.com",
            role="driver",
            password="TestPassword123!"
        )
        
        mock_user_repository.find_by_email.return_value = {"email": "test@example.com"}
        
        with patch('services.user_service.UserRepository', mock_user_repository):
            with pytest.raises(ValueError, match="User with this email already exists"):
                await UserService.create_user_manually(user_data, "admin-user-123")
    
    @pytest.mark.asyncio
    async def test_update_user_permissions(self, mock_user_repository, mock_audit_repository):
        """Test updating user permissions."""
        user_id = "test-user-123"
        new_role = "fleet_manager"
        admin_user_id = "admin-user-123"
        
        mock_user_repository.find_by_id.return_value = {"user_id": user_id, "role": "driver"}
        mock_user_repository.update_user.return_value = True
        
        with patch('services.user_service.UserRepository', mock_user_repository), \
             patch('services.user_service.AuditRepository', mock_audit_repository):
            
            result = await UserService.update_user_permissions(user_id, new_role, admin_user_id)
            
            assert result["message"] == "User permissions updated successfully"
            mock_user_repository.update_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user(self, mock_user_repository, mock_audit_repository):
        """Test user deletion."""
        user_id = "test-user-123"
        admin_user_id = "admin-user-123"
        
        mock_user_repository.find_by_id.return_value = {"user_id": user_id}
        mock_user_repository.delete_user.return_value = True
        
        with patch('services.user_service.UserRepository', mock_user_repository), \
             patch('services.user_service.AuditRepository', mock_audit_repository):
            
            result = await UserService.delete_user(user_id, admin_user_id)
            
            assert result["message"] == "User deleted successfully"
            mock_user_repository.delete_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self):
        """Test updating user profile."""
        # TODO: Implement profile update tests
        pass
    
    @pytest.mark.asyncio
    async def test_change_user_password(self):
        """Test changing user password."""
        # TODO: Implement password change tests
        pass
