"""
Utility functions and classes for the GPS Service.
Contains common functionality that can be reused across different parts of the service.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from logging_config import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages environment configuration for the service."""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """
        Get service configuration from environment variables.
        
        Returns:
            Dictionary containing service configuration
        """
        config = {
            "service_name": os.getenv("SERVICE_NAME", "gps-service"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
            "debug": os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
            
            # Database configurations
            "redis": {
                "host": os.getenv("REDIS_HOST", "redis"),
                "port": int(os.getenv("REDIS_PORT", "6379")),
                "db": int(os.getenv("REDIS_DB", "0")),
                "password": os.getenv("REDIS_PASSWORD"),
                "timeout": int(os.getenv("REDIS_TIMEOUT", "5"))
            },
            
            # Message queue configurations
            "rabbitmq": {
                "host": os.getenv("RABBITMQ_HOST", "rabbitmq"),
                "port": int(os.getenv("RABBITMQ_PORT", "5672")),
                "username": os.getenv("RABBITMQ_USERNAME", "guest"),
                "password": os.getenv("RABBITMQ_PASSWORD", "guest"),
                "virtual_host": os.getenv("RABBITMQ_VHOST", "/")
            },
            
            # API configurations
            "api": {
                "host": os.getenv("API_HOST", "0.0.0.0"),
                "port": int(os.getenv("API_PORT", "8000")),
                "workers": int(os.getenv("API_WORKERS", "1")),
                "cors_origins": os.getenv("CORS_ORIGINS", "*").split(",")
            }
        }
        
        return config
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development environment."""
        return os.getenv("ENVIRONMENT", "development").lower() == "development"


class ResponseFormatter:
    """Formats API responses consistently across the service."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Format a successful API response.
        
        Args:
            data: Response data
            message: Success message
            metadata: Additional metadata
            
        Returns:
            Formatted response dictionary
        """
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if data is not None:
            response["data"] = data
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def error(message: str, error_code: Optional[str] = None, details: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Format an error API response.
        
        Args:
            message: Error message
            error_code: Optional error code
            details: Additional error details
            
        Returns:
            Formatted error response dictionary
        """
        response = {
            "success": False,
            "error": {
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        if error_code:
            response["error"]["code"] = error_code
        
        if details:
            response["error"]["details"] = details
        
        return response
    
    @staticmethod
    def paginated(data: list, page: int, page_size: int, total: int, message: str = "Success") -> Dict[str, Any]:
        """
        Format a paginated API response.
        
        Args:
            data: List of items for current page
            page: Current page number (1-based)
            page_size: Number of items per page
            total: Total number of items
            message: Success message
            
        Returns:
            Formatted paginated response dictionary
        """
        total_pages = (total + page_size - 1) // page_size  # Ceiling division
        
        return {
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }


class DataValidator:
    """Validates input data for API endpoints."""
    
    @staticmethod
    def validate_gps_coordinates(lat: float, lon: float) -> bool:
        """
        Validate GPS coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    @staticmethod
    def validate_required_fields(data: Dict, required_fields: list) -> tuple[bool, Optional[str]]:
        """
        Validate that required fields are present in data.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, None


class CacheManager:
    """Manages caching operations with Redis."""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if not self.redis_client:
                return None
            
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False
            
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False
            
            return bool(self.redis_client.delete(key))
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            if not self.redis_client:
                return False
            
            return bool(self.redis_client.exists(key))
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False


# Convenience functions
def get_config():
    """Get service configuration - convenience function."""
    return ConfigManager.get_config()


def format_success_response(data=None, message="Success", metadata=None):
    """Format success response - convenience function."""
    return ResponseFormatter.success(data, message, metadata)


def format_error_response(message, error_code=None, details=None):
    """Format error response - convenience function."""
    return ResponseFormatter.error(message, error_code, details)
