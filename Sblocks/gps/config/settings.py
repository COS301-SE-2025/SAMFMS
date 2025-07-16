"""
Configuration for GPS service
"""
import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class SecurityConfig(BaseModel):
    """Security configuration"""
    enable_hsts: bool = Field(default=True, description="Enable HSTS headers")
    hsts_max_age: int = Field(default=31536000, description="HSTS max age in seconds")
    rate_limit_requests_per_minute: int = Field(default=120, description="Rate limit per minute")
    enable_cors: bool = Field(default=True, description="Enable CORS")
    allowed_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")


class DatabaseConfig(BaseModel):
    """Database configuration"""
    mongodb_url: str = Field(
        default="mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017",
        description="MongoDB connection URL"
    )
    database_name: str = Field(default="samfms_gps", description="Database name")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    max_pool_size: int = Field(default=100, description="Maximum connection pool size")


class RabbitMQConfig(BaseModel):
    """RabbitMQ configuration"""
    rabbitmq_url: str = Field(
        default="amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/",
        description="RabbitMQ connection URL"
    )
    heartbeat: int = Field(default=600, description="Heartbeat interval in seconds")
    blocked_connection_timeout: int = Field(default=300, description="Blocked connection timeout")
    connection_attempts: int = Field(default=3, description="Connection retry attempts")
    retry_delay: float = Field(default=2.0, description="Retry delay in seconds")
    max_retry_attempts: int = Field(default=3, description="Max message retry attempts")
    prefetch_count: int = Field(default=10, description="Message prefetch count")


class GPSConfig(BaseModel):
    """GPS-specific configuration"""
    location_history_days: int = Field(default=90, description="Days to keep location history")
    geofence_check_enabled: bool = Field(default=True, description="Enable geofence checking")
    real_time_tracking: bool = Field(default=True, description="Enable real-time tracking")
    max_tracking_sessions_per_user: int = Field(default=10, description="Max tracking sessions per user")


class ServiceConfig(BaseModel):
    """Main service configuration"""
    service_name: str = Field(default="gps", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8000, description="Service port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Sub-configurations
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig)
    gps: GPSConfig = Field(default_factory=GPSConfig)


def load_config() -> ServiceConfig:
    """Load configuration from environment variables"""
    return ServiceConfig(
        service_name=os.getenv("SERVICE_NAME", "gps"),
        version=os.getenv("SERVICE_VERSION", "1.0.0"),
        host=os.getenv("GPS_HOST", "0.0.0.0"),
        port=int(os.getenv("GPS_PORT", "8000")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        
        security=SecurityConfig(
            rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "120")),
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "*").split(",")
        ),
        
        database=DatabaseConfig(
            mongodb_url=os.getenv(
                "MONGODB_URL",
                "mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017"
            ),
            database_name=os.getenv("DATABASE_NAME", "samfms_gps"),
            max_pool_size=int(os.getenv("DB_MAX_POOL_SIZE", "100"))
        ),
        
        rabbitmq=RabbitMQConfig(
            rabbitmq_url=os.getenv(
                "RABBITMQ_URL",
                "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"
            ),
            heartbeat=int(os.getenv("RABBITMQ_HEARTBEAT", "600")),
            connection_attempts=int(os.getenv("RABBITMQ_CONNECTION_ATTEMPTS", "3"))
        ),
        
        gps=GPSConfig(
            location_history_days=int(os.getenv("LOCATION_HISTORY_DAYS", "90")),
            geofence_check_enabled=os.getenv("GEOFENCE_CHECK_ENABLED", "true").lower() == "true",
            real_time_tracking=os.getenv("REAL_TIME_TRACKING", "true").lower() == "true"
        )
    )


# Global configuration instance
config = load_config()
