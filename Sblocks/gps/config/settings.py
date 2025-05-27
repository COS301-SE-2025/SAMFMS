"""
GPS Service Configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="GPS Tracking Service", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8002, env="PORT")  # Different port from trip_planning
    reload: bool = Field(default=True, env="RELOAD")
    
    # Database
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="gps_tracking", env="MONGODB_DATABASE")
    mongodb_min_pool_size: int = Field(default=5, env="MONGODB_MIN_POOL_SIZE")
    mongodb_max_pool_size: int = Field(default=50, env="MONGODB_MAX_POOL_SIZE")
    
    # Redis for caching and real-time data
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=1, env="REDIS_DB")  # Different DB from trip_planning
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # RabbitMQ for messaging
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", env="RABBITMQ_URL")
    rabbitmq_exchange: str = Field(default="gps_exchange", env="RABBITMQ_EXCHANGE")
    rabbitmq_queue_prefix: str = Field(default="gps", env="RABBITMQ_QUEUE_PREFIX")
    
    # Location tracking settings
    location_update_interval: int = Field(default=30, env="LOCATION_UPDATE_INTERVAL")  # seconds
    location_buffer_size: int = Field(default=100, env="LOCATION_BUFFER_SIZE")
    location_retention_days: int = Field(default=90, env="LOCATION_RETENTION_DAYS")
    high_frequency_tracking: bool = Field(default=False, env="HIGH_FREQUENCY_TRACKING")
    
    # Geofencing settings
    geofence_check_interval: int = Field(default=10, env="GEOFENCE_CHECK_INTERVAL")  # seconds
    geofence_buffer_distance: float = Field(default=50.0, env="GEOFENCE_BUFFER_DISTANCE")  # meters
    max_geofences_per_vehicle: int = Field(default=50, env="MAX_GEOFENCES_PER_VEHICLE")
    
    # Real-time settings
    websocket_enabled: bool = Field(default=True, env="WEBSOCKET_ENABLED")
    websocket_path: str = Field(default="/ws", env="WEBSOCKET_PATH")
    real_time_updates: bool = Field(default=True, env="REAL_TIME_UPDATES")
    
    # Security
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    secret_key: str = Field(default="gps-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # External services
    trip_planning_service_url: str = Field(default="http://localhost:8001", env="TRIP_PLANNING_SERVICE_URL")
    mcore_service_url: str = Field(default="http://localhost:8000", env="MCORE_SERVICE_URL")
    
    # Analytics and monitoring
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    analytics_batch_size: int = Field(default=1000, env="ANALYTICS_BATCH_SIZE")
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/gps_service.log", env="LOG_FILE")
    log_rotation: str = Field(default="1 day", env="LOG_ROTATION")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    # Performance settings
    max_concurrent_connections: int = Field(default=1000, env="MAX_CONCURRENT_CONNECTIONS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    batch_processing_size: int = Field(default=500, env="BATCH_PROCESSING_SIZE")
    
    # Additional fields
    gps_service_env: str = Field(default="development", env="GPS_SERVICE_ENV")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8003, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    location_accuracy_threshold: float = Field(default=50.0, env="LOCATION_ACCURACY_THRESHOLD")
    enable_real_time_tracking: bool = Field(default=True, env="ENABLE_REAL_TIME_TRACKING")
    enable_geofence_monitoring: bool = Field(default=True, env="ENABLE_GEOFENCE_MONITORING")
    max_workers: int = Field(default=10, env="MAX_WORKERS")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8004, env="METRICS_PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "forbid"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    @property
    def database_url(self) -> str:
        return f"{self.mongodb_url}/{self.mongodb_database}"

# Global settings instance
settings = Settings()

# Database collection names
class Collections:
    VEHICLE_LOCATIONS = "vehicle_locations"
    LOCATION_HISTORY = "location_history"
    GEOFENCES = "geofences"
    GEOFENCE_EVENTS = "geofence_events"
    VEHICLE_ROUTES = "vehicle_routes"
    ROUTE_SEGMENTS = "route_segments"
    PLANNED_ROUTES = "planned_routes"
    ANALYTICS = "analytics"
    ALERTS = "alerts"

collections = Collections()

# Event types for messaging
class EventTypes:
    LOCATION_UPDATED = "location.updated"
    GEOFENCE_ENTERED = "geofence.entered"
    GEOFENCE_EXITED = "geofence.exited"
    SPEED_VIOLATION = "speed.violation"
    ROUTE_STARTED = "route.started"
    ROUTE_COMPLETED = "route.completed"
    VEHICLE_IDLE = "vehicle.idle"
    EMERGENCY_ALERT = "emergency.alert"

event_types = EventTypes()

def get_settings() -> Settings:
    return Settings()
