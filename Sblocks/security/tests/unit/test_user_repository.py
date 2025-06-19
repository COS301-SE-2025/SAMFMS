"""Unit tests for UserRepository."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from repositories.user_repository import UserRepository


class TestUserRepository:
    """Test UserRepository functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, mock_database, test_user_data):
        """Test user creation in database."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_collection.insert_one.return_value = MagicMock(inserted_id="user_123")
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.create_user(test_user_data)
            
            assert result is not None
            mock_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_email(self, mock_database, test_user_data):
        """Test finding user by email."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_collection.find_one.return_value = test_user_data
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.find_by_email(test_user_data["email"])
            
            assert result == test_user_data
            mock_collection.find_one.assert_called_once_with({"email": test_user_data["email"]})
    
    @pytest.mark.asyncio
    async def test_find_by_id(self, mock_database, test_user_data):
        """Test finding user by ID."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_collection.find_one.return_value = test_user_data
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.find_by_id(test_user_data["user_id"])
            
            assert result == test_user_data
            mock_collection.find_one.assert_called_once_with({"user_id": test_user_data["user_id"]})
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, mock_database, test_user_data, test_admin_user_data):
        """Test getting all users."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [test_user_data, test_admin_user_data]
        mock_collection.find.return_value = mock_cursor
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.get_all_users()
            
            assert len(result) == 2
            mock_collection.find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user(self, mock_database, test_user_data):
        """Test updating user in database."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        
        update_data = {"role": "fleet_manager"}
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.update_user(test_user_data["user_id"], update_data)
            
            assert result is True
            mock_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user(self, mock_database, test_user_data):
        """Test deleting user from database."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.delete_user(test_user_data["user_id"])
            
            assert result is True
            mock_collection.delete_one.assert_called_once_with({"user_id": test_user_data["user_id"]})
    
    @pytest.mark.asyncio
    async def test_find_users_by_role(self, mock_database):
        """Test finding users by role."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [{"user_id": "driver1", "role": "driver"}]
        mock_collection.find.return_value = mock_cursor
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.find_users_by_role("driver")
            
            assert len(result) == 1
            assert result[0]["role"] == "driver"
            mock_collection.find.assert_called_once_with({"role": "driver"})
    
    @pytest.mark.asyncio
    async def test_update_last_login(self, mock_database, test_user_data):
        """Test updating user's last login timestamp."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.update_last_login(test_user_data["user_id"])
            
            assert result is True
            mock_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_users_by_role(self, mock_database):
        """Test counting users by role."""
        mock_collection = AsyncMock()
        mock_database.users = mock_collection
        mock_collection.count_documents.return_value = 5
        
        with patch('repositories.user_repository.get_database', return_value=mock_database):
            result = await UserRepository.count_users_by_role("admin")
            
            assert result == 5
            mock_collection.count_documents.assert_called_once_with({"role": "admin"})
