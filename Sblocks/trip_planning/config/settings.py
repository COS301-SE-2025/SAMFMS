from pydantic_settings import BaseSettings
import os
from typing import Optional


class TripPlanningSettings(BaseSettings):
    """Trip Planning Service Configuration"""
    
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://mongodb:27017"
    DATABASE_NAME: str = "trip_planning_db"
    
    # RabbitMQ Configuration
    RABBITMQ_URL: str = "amqp://user:password@rabbitmq:5672/"
    RABBITMQ_EXCHANGE: str = "samfms_exchange"
    RABBITMQ_QUEUE_PREFIX: str = "trip_planning"
    
    # Service Configuration
    SERVICE_NAME: str = "trip_planning"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8000
    SERVICE_HOST: str = "0.0.0.0"
    
    # External Service URLs
    GPS_SERVICE_URL: str = "http://gps-service:8000"
    USER_SERVICE_URL: str = "http://users-service:8000"
    VEHICLE_SERVICE_URL: str = "http://vehicles-service:8000"
    
    # Redis Configuration (for caching)
    REDIS_URL: str = "redis://redis:6379"
    REDIS_TTL: int = 300  # 5 minutes default TTL
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["*"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance Settings
    MAX_CONNECTIONS_PER_HOST: int = 10
    REQUEST_TIMEOUT: int = 30
    MAX_RETRY_ATTEMPTS: int = 3
    
    # Route Calculation Settings
    MAX_WAYPOINTS: int = 25
    MAX_TRIP_DURATION_HOURS: int = 24
    DEFAULT_VEHICLE_SPEED_KMH: int = 60
    
    # Driver Assignment Settings
    MAX_DRIVING_HOURS_PER_DAY: int = 10
    MIN_REST_HOURS: int = 8
    MAX_ASSIGNMENTS_PER_DRIVER: int = 3
    
    # Notification Settings
    NOTIFICATION_RETRY_ATTEMPTS: int = 3
    NOTIFICATION_TIMEOUT: int = 10
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = TripPlanningSettings()


def get_settings() -> TripPlanningSettings:
    """Get application settings"""
    return settings


def get_database_url() -> str:
    """Get database connection URL"""
    return settings.MONGODB_URL


def get_rabbitmq_url() -> str:
    """Get RabbitMQ connection URL"""
    return settings.RABBITMQ_URL
