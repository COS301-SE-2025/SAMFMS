"""Configuration settings for trip planning service"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    app_name: str = "Trip Planning Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8003, env="PORT")
    
    # Database Configuration
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    database_name: str = Field(default="trip_planning_db", env="DATABASE_NAME")
    
    # Collection Names
    trips_collection: str = "trips"
    vehicles_collection: str = "vehicles"
    drivers_collection: str = "drivers"
    routes_collection: str = "routes"
    schedules_collection: str = "schedules"
    
    # RabbitMQ Configuration
    rabbitmq_url: str = Field(default="amqp://guest:guest@localhost:5672/", env="RABBITMQ_URL")
    exchange_name: str = Field(default="mcore_exchange", env="EXCHANGE_NAME")
    queue_name: str = Field(default="trip_planning_queue", env="QUEUE_NAME")
    
    # Redis Configuration (for caching)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Security Settings
    secret_key: str = Field(default="your-secret-key-change-this", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # API Configuration
    api_v1_str: str = "/api/v1"
    cors_origins: list = Field(default=["http://localhost:3000", "http://localhost:8080"], env="CORS_ORIGINS")
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Route Optimization
    default_speed_kmh: float = 50.0
    fuel_cost_per_liter: float = Field(default=1.5, env="FUEL_COST_PER_LITER")
    driver_cost_per_hour: float = Field(default=15.0, env="DRIVER_COST_PER_HOUR")
    vehicle_efficiency_default: float = 12.0  # km per liter
    
    # Schedule Configuration
    working_hours_start: int = 6  # 6 AM
    working_hours_end: int = 22   # 10 PM
    max_daily_hours: int = 10
    min_break_minutes: int = 30
    
    # Notification Settings
    email_enabled: bool = Field(default=False, env="EMAIL_ENABLED")
    smtp_server: str = Field(default="localhost", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: str = Field(default="", env="SMTP_USER")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    
    # External API Keys
    google_maps_api_key: Optional[str] = Field(default=None, env="GOOGLE_MAPS_API_KEY")
    weather_api_key: Optional[str] = Field(default=None, env="WEATHER_API_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Health Check
    health_check_interval: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def get_database_url(self) -> str:
        """Get complete database URL"""
        return f"{self.mongodb_url}/{self.database_name}"
    
    def get_cors_origins(self) -> list:
        """Get CORS origins as list"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins


# Global settings instance
settings = Settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    log_level: str = "WARNING"
    
    # Override with more secure defaults for production
    secret_key: str = Field(env="SECRET_KEY")  # Must be provided in production
    mongodb_url: str = Field(env="MONGODB_URL")  # Must be provided in production
    rabbitmq_url: str = Field(env="RABBITMQ_URL")  # Must be provided in production


class TestSettings(Settings):
    """Test environment settings"""
    debug: bool = True
    database_name: str = "trip_planning_test_db"
    mongodb_url: str = "mongodb://localhost:27017"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    cache_ttl: int = 60  # Shorter cache for tests


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# Create settings instance
settings = get_settings()
