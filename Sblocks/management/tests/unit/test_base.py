"""
Unit tests for base repository
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from repositories.base import BaseRepository


class TestRepository(BaseRepository):
    """Test implementation of BaseRepository"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        super().__init__(collection)


@pytest.mark.unit
@pytest.mark.repository
class TestBaseRepository:
    """Test class for BaseRepository"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_collection = AsyncMock(spec=AsyncIOMotorCollection)
        self.repository = TestRepository(self.mock_collection)
        
        # Mock data
        self.test_id = ObjectId()
        self.test_entity = {
            "_id": self.test_id,
            "name": "Test Entity",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    
    @pytest.mark.asyncio
    async def test_create_entity_success(self):
        """Test creating entity successfully"""
        # Arrange
        entity_data = {
            "name": "New Entity",
            "status": "active"
        }
        
        self.mock_collection.insert_one.return_value = AsyncMock()
        self.mock_collection.insert_one.return_value.inserted_id = self.test_id
        
        # Act
        result = await self.repository.create(entity_data)
        
        # Assert
        assert result == str(self.test_id)
        self.mock_collection.insert_one.assert_called_once()
        
        # Check that timestamps were added
        call_args = self.mock_collection.insert_one.call_args[0][0]
        assert "created_at" in call_args
        assert "updated_at" in call_args
    
    @pytest.mark.asyncio
    async def test_create_entity_with_existing_timestamps(self):
        """Test creating entity with existing timestamps"""
        # Arrange
        existing_time = datetime.now(timezone.utc)
        entity_data = {
            "name": "New Entity",
            "status": "active",
            "created_at": existing_time,
            "updated_at": existing_time
        }
        
        self.mock_collection.insert_one.return_value = AsyncMock()
        self.mock_collection.insert_one.return_value.inserted_id = self.test_id
        
        # Act
        result = await self.repository.create(entity_data)
        
        # Assert
        assert result == str(self.test_id)
        call_args = self.mock_collection.insert_one.call_args[0][0]
        assert call_args["created_at"] == existing_time
        assert call_args["updated_at"] == existing_time
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        """Test getting entity by ID when found"""
        # Arrange
        self.mock_collection.find_one.return_value = self.test_entity
        
        # Act
        result = await self.repository.get_by_id(str(self.test_id))
        
        # Assert
        assert result == self.test_entity
        self.mock_collection.find_one.assert_called_once_with({"_id": self.test_id})
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test getting entity by ID when not found"""
        # Arrange
        self.mock_collection.find_one.return_value = None
        
        # Act
        result = await self.repository.get_by_id(str(self.test_id))
        
        # Assert
        assert result is None
        self.mock_collection.find_one.assert_called_once_with({"_id": self.test_id})
    
    @pytest.mark.asyncio
    async def test_get_by_id_invalid_object_id(self):
        """Test getting entity by invalid ObjectId"""
        # Arrange
        invalid_id = "invalid_id"
        
        # Act & Assert
        with pytest.raises(ValueError):
            await self.repository.get_by_id(invalid_id)
    
    @pytest.mark.asyncio
    async def test_get_all_entities(self):
        """Test getting all entities"""
        # Arrange
        entities = [self.test_entity, {**self.test_entity, "_id": ObjectId()}]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = entities
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_all()
        
        # Assert
        assert result == entities
        self.mock_collection.find.assert_called_once_with({})
        mock_cursor.to_list.assert_called_once_with(None)
    
    @pytest.mark.asyncio
    async def test_get_all_entities_with_filter(self):
        """Test getting all entities with filter"""
        # Arrange
        filter_criteria = {"status": "active"}
        entities = [self.test_entity]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = entities
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_all(filter_criteria)
        
        # Assert
        assert result == entities
        self.mock_collection.find.assert_called_once_with(filter_criteria)
    
    @pytest.mark.asyncio
    async def test_get_all_entities_with_pagination(self):
        """Test getting all entities with pagination"""
        # Arrange
        entities = [self.test_entity]
        mock_cursor = AsyncMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list.return_value = entities
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_all({}, skip=10, limit=5)
        
        # Assert
        assert result == entities
        self.mock_collection.find.assert_called_once_with({})
        mock_cursor.skip.assert_called_once_with(10)
        mock_cursor.limit.assert_called_once_with(5)
    
    @pytest.mark.asyncio
    async def test_get_all_entities_with_sort(self):
        """Test getting all entities with sorting"""
        # Arrange
        entities = [self.test_entity]
        mock_cursor = AsyncMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.to_list.return_value = entities
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_all({}, sort=[("created_at", -1)])
        
        # Assert
        assert result == entities
        self.mock_collection.find.assert_called_once_with({})
        mock_cursor.sort.assert_called_once_with([("created_at", -1)])
    
    @pytest.mark.asyncio
    async def test_update_entity_success(self):
        """Test updating entity successfully"""
        # Arrange
        update_data = {"name": "Updated Entity", "status": "inactive"}
        
        mock_result = AsyncMock()
        mock_result.modified_count = 1
        self.mock_collection.update_one.return_value = mock_result
        
        # Act
        result = await self.repository.update(str(self.test_id), update_data)
        
        # Assert
        assert result is True
        self.mock_collection.update_one.assert_called_once()
        
        # Check that updated_at was added
        call_args = self.mock_collection.update_one.call_args[0][1]
        assert "updated_at" in call_args["$set"]
    
    @pytest.mark.asyncio
    async def test_update_entity_not_found(self):
        """Test updating entity that doesn't exist"""
        # Arrange
        update_data = {"name": "Updated Entity"}
        
        mock_result = AsyncMock()
        mock_result.modified_count = 0
        self.mock_collection.update_one.return_value = mock_result
        
        # Act
        result = await self.repository.update(str(self.test_id), update_data)
        
        # Assert
        assert result is False
        self.mock_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_entity_invalid_object_id(self):
        """Test updating entity with invalid ObjectId"""
        # Arrange
        invalid_id = "invalid_id"
        update_data = {"name": "Updated Entity"}
        
        # Act & Assert
        with pytest.raises(ValueError):
            await self.repository.update(invalid_id, update_data)
    
    @pytest.mark.asyncio
    async def test_delete_entity_success(self):
        """Test deleting entity successfully"""
        # Arrange
        mock_result = AsyncMock()
        mock_result.deleted_count = 1
        self.mock_collection.delete_one.return_value = mock_result
        
        # Act
        result = await self.repository.delete(str(self.test_id))
        
        # Assert
        assert result is True
        self.mock_collection.delete_one.assert_called_once_with({"_id": self.test_id})
    
    @pytest.mark.asyncio
    async def test_delete_entity_not_found(self):
        """Test deleting entity that doesn't exist"""
        # Arrange
        mock_result = AsyncMock()
        mock_result.deleted_count = 0
        self.mock_collection.delete_one.return_value = mock_result
        
        # Act
        result = await self.repository.delete(str(self.test_id))
        
        # Assert
        assert result is False
        self.mock_collection.delete_one.assert_called_once_with({"_id": self.test_id})
    
    @pytest.mark.asyncio
    async def test_delete_entity_invalid_object_id(self):
        """Test deleting entity with invalid ObjectId"""
        # Arrange
        invalid_id = "invalid_id"
        
        # Act & Assert
        with pytest.raises(ValueError):
            await self.repository.delete(invalid_id)
    
    @pytest.mark.asyncio
    async def test_count_entities(self):
        """Test counting entities"""
        # Arrange
        self.mock_collection.count_documents.return_value = 10
        
        # Act
        result = await self.repository.count()
        
        # Assert
        assert result == 10
        self.mock_collection.count_documents.assert_called_once_with({})
    
    @pytest.mark.asyncio
    async def test_count_entities_with_filter(self):
        """Test counting entities with filter"""
        # Arrange
        filter_criteria = {"status": "active"}
        self.mock_collection.count_documents.return_value = 5
        
        # Act
        result = await self.repository.count(filter_criteria)
        
        # Assert
        assert result == 5
        self.mock_collection.count_documents.assert_called_once_with(filter_criteria)
    
    @pytest.mark.asyncio
    async def test_exists_entity_found(self):
        """Test checking if entity exists when found"""
        # Arrange
        self.mock_collection.find_one.return_value = self.test_entity
        
        # Act
        result = await self.repository.exists(str(self.test_id))
        
        # Assert
        assert result is True
        self.mock_collection.find_one.assert_called_once_with({"_id": self.test_id})
    
    @pytest.mark.asyncio
    async def test_exists_entity_not_found(self):
        """Test checking if entity exists when not found"""
        # Arrange
        self.mock_collection.find_one.return_value = None
        
        # Act
        result = await self.repository.exists(str(self.test_id))
        
        # Assert
        assert result is False
        self.mock_collection.find_one.assert_called_once_with({"_id": self.test_id})
    
    @pytest.mark.asyncio
    async def test_exists_entity_invalid_object_id(self):
        """Test checking if entity exists with invalid ObjectId"""
        # Arrange
        invalid_id = "invalid_id"
        
        # Act & Assert
        with pytest.raises(ValueError):
            await self.repository.exists(invalid_id)
    
    @pytest.mark.asyncio
    async def test_find_one_entity_found(self):
        """Test finding one entity with filter"""
        # Arrange
        filter_criteria = {"name": "Test Entity"}
        self.mock_collection.find_one.return_value = self.test_entity
        
        # Act
        result = await self.repository.find_one(filter_criteria)
        
        # Assert
        assert result == self.test_entity
        self.mock_collection.find_one.assert_called_once_with(filter_criteria)
    
    @pytest.mark.asyncio
    async def test_find_one_entity_not_found(self):
        """Test finding one entity with filter when not found"""
        # Arrange
        filter_criteria = {"name": "Non-existent Entity"}
        self.mock_collection.find_one.return_value = None
        
        # Act
        result = await self.repository.find_one(filter_criteria)
        
        # Assert
        assert result is None
        self.mock_collection.find_one.assert_called_once_with(filter_criteria)
    
    @pytest.mark.asyncio
    async def test_find_many_entities(self):
        """Test finding many entities with filter"""
        # Arrange
        filter_criteria = {"status": "active"}
        entities = [self.test_entity, {**self.test_entity, "_id": ObjectId()}]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = entities
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.find_many(filter_criteria)
        
        # Assert
        assert result == entities
        self.mock_collection.find.assert_called_once_with(filter_criteria)
    
    @pytest.mark.asyncio
    async def test_bulk_create_entities(self):
        """Test bulk creating entities"""
        # Arrange
        entities_data = [
            {"name": "Entity 1", "status": "active"},
            {"name": "Entity 2", "status": "inactive"}
        ]
        
        mock_result = AsyncMock()
        mock_result.inserted_ids = [ObjectId(), ObjectId()]
        self.mock_collection.insert_many.return_value = mock_result
        
        # Act
        result = await self.repository.bulk_create(entities_data)
        
        # Assert
        assert len(result) == 2
        self.mock_collection.insert_many.assert_called_once()
        
        # Check that timestamps were added to all entities
        call_args = self.mock_collection.insert_many.call_args[0][0]
        for entity in call_args:
            assert "created_at" in entity
            assert "updated_at" in entity
    
    @pytest.mark.asyncio
    async def test_bulk_update_entities(self):
        """Test bulk updating entities"""
        # Arrange
        filter_criteria = {"status": "active"}
        update_data = {"status": "inactive"}
        
        mock_result = AsyncMock()
        mock_result.modified_count = 3
        self.mock_collection.update_many.return_value = mock_result
        
        # Act
        result = await self.repository.bulk_update(filter_criteria, update_data)
        
        # Assert
        assert result == 3
        self.mock_collection.update_many.assert_called_once()
        
        # Check that updated_at was added
        call_args = self.mock_collection.update_many.call_args[0][1]
        assert "updated_at" in call_args["$set"]
    
    @pytest.mark.asyncio
    async def test_bulk_delete_entities(self):
        """Test bulk deleting entities"""
        # Arrange
        filter_criteria = {"status": "inactive"}
        
        mock_result = AsyncMock()
        mock_result.deleted_count = 2
        self.mock_collection.delete_many.return_value = mock_result
        
        # Act
        result = await self.repository.bulk_delete(filter_criteria)
        
        # Assert
        assert result == 2
        self.mock_collection.delete_many.assert_called_once_with(filter_criteria)
    
    @pytest.mark.asyncio
    async def test_aggregate_entities(self):
        """Test aggregating entities"""
        # Arrange
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        aggregation_result = [{"_id": "active", "count": 5}]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = aggregation_result
        self.mock_collection.aggregate.return_value = mock_cursor
        
        # Act
        result = await self.repository.aggregate(pipeline)
        
        # Assert
        assert result == aggregation_result
        self.mock_collection.aggregate.assert_called_once_with(pipeline)
    
    @pytest.mark.asyncio
    async def test_distinct_values(self):
        """Test getting distinct values"""
        # Arrange
        field = "status"
        distinct_values = ["active", "inactive", "maintenance"]
        self.mock_collection.distinct.return_value = distinct_values
        
        # Act
        result = await self.repository.distinct(field)
        
        # Assert
        assert result == distinct_values
        self.mock_collection.distinct.assert_called_once_with(field, {})
    
    @pytest.mark.asyncio
    async def test_distinct_values_with_filter(self):
        """Test getting distinct values with filter"""
        # Arrange
        field = "status"
        filter_criteria = {"department": "operations"}
        distinct_values = ["active", "inactive"]
        self.mock_collection.distinct.return_value = distinct_values
        
        # Act
        result = await self.repository.distinct(field, filter_criteria)
        
        # Assert
        assert result == distinct_values
        self.mock_collection.distinct.assert_called_once_with(field, filter_criteria)
    
    @pytest.mark.asyncio
    async def test_repository_error_handling(self):
        """Test repository error handling"""
        # Arrange
        self.mock_collection.find_one.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception):
            await self.repository.get_by_id(str(self.test_id))
    
    @pytest.mark.asyncio
    async def test_repository_connection_handling(self):
        """Test repository connection handling"""
        # Arrange
        self.mock_collection.find_one.side_effect = ConnectionError("Connection lost")
        
        # Act & Assert
        with pytest.raises(ConnectionError):
            await self.repository.get_by_id(str(self.test_id))
    
    def test_repository_initialization(self):
        """Test repository initialization"""
        # Act
        repository = TestRepository(self.mock_collection)
        
        # Assert
        assert repository.collection == self.mock_collection
    
    def test_repository_collection_property(self):
        """Test repository collection property"""
        # Act
        collection = self.repository.collection
        
        # Assert
        assert collection == self.mock_collection
    
    @pytest.mark.asyncio
    async def test_repository_transaction_support(self):
        """Test repository transaction support"""
        # Arrange
        # This test depends on actual transaction implementation
        # For now, we'll test that the repository can handle transaction-like operations
        
        entities_data = [
            {"name": "Entity 1", "status": "active"},
            {"name": "Entity 2", "status": "active"}
        ]
        
        mock_result = AsyncMock()
        mock_result.inserted_ids = [ObjectId(), ObjectId()]
        self.mock_collection.insert_many.return_value = mock_result
        
        # Act
        result = await self.repository.bulk_create(entities_data)
        
        # Assert
        assert len(result) == 2
        self.mock_collection.insert_many.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_repository_index_operations(self):
        """Test repository index operations"""
        # Arrange
        # This test would depend on actual index implementation
        # For now, we'll test that the repository can handle index-related operations
        
        filter_criteria = {"status": "active"}
        entities = [self.test_entity]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = entities
        self.mock_collection.find.return_value = mock_cursor
        
        # Act
        result = await self.repository.get_all(filter_criteria)
        
        # Assert
        assert result == entities
        self.mock_collection.find.assert_called_once_with(filter_criteria)
