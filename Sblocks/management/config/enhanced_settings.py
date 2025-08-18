"""
Enhanced configuration for Management Service
"""
import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from datetime import timedelta


class SecurityConfig(BaseModel):
    """Security configuration"""
    enable_hsts: bool = Field(default=True, description="Enable HSTS headers")
    hsts_max_age: int = Field(default=31536000, description="HSTS max age in seconds")
    rate_limit_requests_per_minute: int = Field(default=120, description="Rate limit per minute")
    enable_cors: bool = Field(default=True, description="Enable CORS")
    allowed_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")


class DatabaseConfig(BaseModel):
    """Database configuration"""
    mongodb_url: str = Field(default="mongodb://localhost:27017", description="MongoDB connection URL")
    database_name: str = Field(default="samfms_management", description="Database name")
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


class CacheConfig(BaseModel):
    """Cache configuration"""
    default_ttl_minutes: int = Field(default=15, description="Default cache TTL in minutes")
    fleet_utilization_ttl: int = Field(default=10, description="Fleet utilization cache TTL")
    vehicle_usage_ttl: int = Field(default=15, description="Vehicle usage cache TTL")
    assignment_metrics_ttl: int = Field(default=5, description="Assignment metrics cache TTL")
    driver_performance_ttl: int = Field(default=30, description="Driver performance cache TTL")
    cost_analytics_ttl: int = Field(default=60, description="Cost analytics cache TTL")


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Log level")
    include_request_body: bool = Field(default=False, description="Include request body in logs")
    include_response_body: bool = Field(default=False, description="Include response body in logs")
    enable_structured_logging: bool = Field(default=True, description="Enable structured logging")


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_retention_count: int = Field(default=100, description="Number of metrics to retain")
    health_check_timeout: int = Field(default=30, description="Health check timeout in seconds")
    background_task_interval: int = Field(default=600, description="Background task interval in seconds")


class ServiceConfig(BaseModel):
    """Main service configuration"""
    service_name: str = Field(default="management", description="Service name")
    version: str = Field(default="2.1.0", description="Service version")
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8000, description="Service port")
    debug: bool = Field(default=False, description="Debug mode")
    enable_docs: bool = Field(default=True, description="Enable API documentation")
    
    # Sub-configurations
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


def load_config() -> ServiceConfig:
    """Load configuration from environment variables"""
    config_dict = {}
    
    # Service settings
    config_dict["service_name"] = os.getenv("SERVICE_NAME", "management")
    config_dict["version"] = os.getenv("SERVICE_VERSION", "2.1.0")
    config_dict["host"] = os.getenv("HOST", "0.0.0.0")
    config_dict["port"] = int(os.getenv("MANAGEMENT_PORT", "8000"))
    config_dict["debug"] = os.getenv("DEBUG", "false").lower() == "true"
    config_dict["enable_docs"] = os.getenv("ENABLE_DOCS", "true").lower() == "true"
    
    # Security settings
    security_config = {
        "enable_hsts": os.getenv("ENABLE_HSTS", "true").lower() == "true",
        "hsts_max_age": int(os.getenv("HSTS_MAX_AGE", "31536000")),
        "rate_limit_requests_per_minute": int(os.getenv("RATE_LIMIT_RPM", "120")),
        "enable_cors": os.getenv("ENABLE_CORS", "true").lower() == "true",
        "allowed_origins": os.getenv("ALLOWED_ORIGINS", "*").split(",")
    }
    config_dict["security"] = security_config
    
    # Database settings
    database_config = {
        "mongodb_url": os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
        "database_name": os.getenv("DATABASE_NAME", "samfms_management"),
        "connection_timeout": int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
        "max_pool_size": int(os.getenv("DB_MAX_POOL_SIZE", "100"))
    }
    config_dict["database"] = database_config
    
    # RabbitMQ settings
    rabbitmq_config = {
        "rabbitmq_url": os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/"),
        "heartbeat": int(os.getenv("RABBITMQ_HEARTBEAT", "600")),
        "blocked_connection_timeout": int(os.getenv("RABBITMQ_BLOCKED_TIMEOUT", "300")),
        "connection_attempts": int(os.getenv("RABBITMQ_CONNECTION_ATTEMPTS", "3")),
        "retry_delay": float(os.getenv("RABBITMQ_RETRY_DELAY", "2.0")),
        "max_retry_attempts": int(os.getenv("RABBITMQ_MAX_RETRIES", "3")),
        "prefetch_count": int(os.getenv("RABBITMQ_PREFETCH_COUNT", "10"))
    }
    config_dict["rabbitmq"] = rabbitmq_config
    
    # Cache settings
    cache_config = {
        "default_ttl_minutes": int(os.getenv("CACHE_DEFAULT_TTL", "15")),
        "fleet_utilization_ttl": int(os.getenv("CACHE_FLEET_TTL", "10")),
        "vehicle_usage_ttl": int(os.getenv("CACHE_VEHICLE_TTL", "15")),
        "assignment_metrics_ttl": int(os.getenv("CACHE_ASSIGNMENT_TTL", "5")),
        "driver_performance_ttl": int(os.getenv("CACHE_DRIVER_TTL", "30")),
        "cost_analytics_ttl": int(os.getenv("CACHE_COST_TTL", "60"))
    }
    config_dict["cache"] = cache_config
    
    # Logging settings
    logging_config = {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "include_request_body": os.getenv("LOG_REQUEST_BODY", "false").lower() == "true",
        "include_response_body": os.getenv("LOG_RESPONSE_BODY", "false").lower() == "true",
        "enable_structured_logging": os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
    }
    config_dict["logging"] = logging_config
    
    # Monitoring settings
    monitoring_config = {
        "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
        "metrics_retention_count": int(os.getenv("METRICS_RETENTION", "100")),
        "health_check_timeout": int(os.getenv("HEALTH_CHECK_TIMEOUT", "30")),
        "background_task_interval": int(os.getenv("BACKGROUND_TASK_INTERVAL", "600"))
    }
    config_dict["monitoring"] = monitoring_config
    
    return ServiceConfig(**config_dict)


# Global configuration instance
config = load_config()


def get_config() -> ServiceConfig:
    """Get the global configuration instance"""
    return config


def reload_config() -> ServiceConfig:
    """Reload configuration from environment"""
    global config
    config = load_config()
    return config
