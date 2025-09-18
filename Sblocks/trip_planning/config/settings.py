"""
Configuration for Trips service
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

class TripsConfig(BaseModel):
    """Trip planning service configuration"""
    trip_history_days: int = Field(default=180, description="Days to retain completed trip records")
    default_optimization: str = Field(default="time", description="Default optimization type (time, distance, cost)")
    max_trips_per_vehicle_per_day: int = Field(default=5, description="Maximum trips a vehicle can handle per day")
    auto_assign_vehicles: bool = Field(default=True, description="Automatically assign vehicles to trips if not provided")
    
    # Speed monitoring configuration
    google_maps_api_key: str = Field(default="", description="Google Maps API key for speed limit checking")
    speed_violation_threshold_kmh: float = Field(default=10.0, description="Speed over limit to trigger violation (km/h)")
    speed_limit_cache_duration: int = Field(default=30, description="Speed limit cache duration in seconds")


class ServiceConfig(BaseModel):
    """Main service configuration"""
    service_name: str = Field(default="trips", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8000, description="Service port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Sub-configurations
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig)
    trips: TripsConfig = Field(default_factory=TripsConfig)

def load_config() -> ServiceConfig:
    """Load configuration from environment variables"""
    return ServiceConfig(
        service_name=os.getenv("SERVICE_NAME", "trips"),
        version=os.getenv("SERVICE_VERSION", "1.0.0"),
        host=os.getenv("TRIPS_HOST", "0.0.0.0"),
        port=int(os.getenv("TRIPS_PORT", "8000")),
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
        
        trips=TripsConfig(
            trip_history_days=int(os.getenv("TRIP_HISTORY_DAYS", "180")),
            default_optimization=os.getenv("DEFAULT_TRIP_OPTIMIZATION", "time"),
            max_trips_per_vehicle_per_day=int(os.getenv("MAX_TRIPS_PER_VEHICLE_PER_DAY", "5")),
            auto_assign_vehicles=os.getenv("AUTO_ASSIGN_VEHICLES", "true").lower() == "true",
            google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", ""),
            speed_violation_threshold_kmh=float(os.getenv("SPEED_VIOLATION_THRESHOLD_KMH", "10.0")),
            speed_limit_cache_duration=int(os.getenv("SPEED_LIMIT_CACHE_DURATION", "30"))
        )

    )


# Global configuration instance
config = load_config()
