"""
Centralized Configuration Management for SAMFMS Core Service
Replaces the dual configuration system with a single, comprehensive solution
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = ""
    name: str = "mcore"
    max_pool_size: int = 50
    min_pool_size: int = 10
    max_idle_time_ms: int = 30000
    connect_timeout_ms: int = 5000
    server_selection_timeout_ms: int = 5000
    socket_timeout_ms: int = 5000

@dataclass
class RabbitMQConfig:
    """RabbitMQ configuration"""
    url: str = ""
    username: str = "samfms_rabbit"
    password: str = ""
    host: str = "rabbitmq"
    port: int = 5672
    management_port: int = 15672
    connection_retry_attempts: int = 30
    connection_retry_delay: int = 2
    heartbeat: int = 600
    blocked_connection_timeout: int = 300

@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = "redis"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    security_service_url: str = ""
    password_min_length: int = 8
    max_login_attempts: int = 5

@dataclass
class ServiceConfig:
    """Service configuration"""
    startup_delay: int = 10
    health_check_interval: int = 30
    request_timeout: int = 30
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

@dataclass
class CoreConfig:
    """Main configuration class"""
    # Core settings
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    core_port: int = 8000
    host: str = "0.0.0.0"
    
    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    rabbitmq: RabbitMQConfig = field(default_factory=RabbitMQConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    service: ServiceConfig = field(default_factory=ServiceConfig)
    
    # Additional settings
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:21015",
        "http://127.0.0.1:21015",
        "https://localhost:21015",
        "https://127.0.0.1:21015"
    ])
    
    @classmethod
    def from_env(cls) -> 'CoreConfig':
        """Create configuration from environment variables"""
        config = cls()
        
        # Core settings
        config.environment = Environment(os.getenv('ENVIRONMENT', 'development'))
        config.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        config.log_level = LogLevel(os.getenv('LOG_LEVEL', 'INFO'))
        config.core_port = int(os.getenv('CORE_PORT', '8000'))
        config.host = os.getenv('HOST', '0.0.0.0')
        
        # Database configuration
        config.database.url = os.getenv('MONGODB_URL', 'mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017')
        config.database.name = os.getenv('DATABASE_NAME', 'samfms_core')
        config.database.max_pool_size = int(os.getenv('DB_MAX_POOL_SIZE', '50'))
        config.database.min_pool_size = int(os.getenv('DB_MIN_POOL_SIZE', '10'))
        
        # RabbitMQ configuration
        config.rabbitmq.url = os.getenv('RABBITMQ_URL', 'amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/')
        config.rabbitmq.username = os.getenv('RABBITMQ_USERNAME', 'samfms_rabbit')
        config.rabbitmq.password = os.getenv('RABBITMQ_PASSWORD', 'RabbitPass2025!')
        config.rabbitmq.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        config.rabbitmq.port = int(os.getenv('RABBITMQ_PORT', '5672'))
        config.rabbitmq.management_port = int(os.getenv('RABBITMQ_MANAGEMENT_PORT', '15672'))
        config.rabbitmq.connection_retry_attempts = int(os.getenv('RABBITMQ_CONNECTION_RETRY_ATTEMPTS', '30'))
        config.rabbitmq.connection_retry_delay = int(os.getenv('RABBITMQ_CONNECTION_RETRY_DELAY', '2'))
        
        # Redis configuration
        config.redis.host = os.getenv('REDIS_HOST', 'redis')
        config.redis.port = int(os.getenv('REDIS_PORT', '6379'))
        config.redis.password = os.getenv('REDIS_PASSWORD')
        config.redis.db = int(os.getenv('REDIS_DB', '0'))
        
        # Security configuration
        config.security.jwt_secret_key = os.getenv('JWT_SECRET_KEY', '')
        config.security.access_token_expire_minutes = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
        config.security.refresh_token_expire_days = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
        config.security.security_service_url = os.getenv('SECURITY_URL', '')
        
        # Service configuration
        config.service.startup_delay = int(os.getenv('SERVICE_STARTUP_DELAY', '10'))
        config.service.health_check_interval = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
        config.service.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        config.service.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        # CORS origins
        cors_origins_env = os.getenv('CORS_ORIGINS', '')
        if cors_origins_env:
            config.cors_origins.extend(cors_origins_env.split(','))
        
        return config
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        errors = []
        warnings = []
        
        # Validate core settings
        if not (1000 <= self.core_port <= 65535):
            errors.append(f"CORE_PORT must be between 1000 and 65535, got {self.core_port}")
        
        # Validate database
        if not self.database.url:
            errors.append("MONGODB_URL is required")
        elif not self.database.url.startswith(('mongodb://', 'mongodb+srv://')):
            errors.append("MONGODB_URL must be a valid MongoDB connection string")
        
        # Validate RabbitMQ
        if not self.rabbitmq.url:
            errors.append("RABBITMQ_URL is required")
        elif not self.rabbitmq.url.startswith('amqp://'):
            errors.append("RABBITMQ_URL must be a valid AMQP connection string")
        
        if not (1000 <= self.rabbitmq.port <= 65535):
            errors.append(f"RABBITMQ_PORT must be between 1000 and 65535, got {self.rabbitmq.port}")
        
        # Validate Redis
        if not (1000 <= self.redis.port <= 65535):
            errors.append(f"REDIS_PORT must be between 1000 and 65535, got {self.redis.port}")
        
        # Validate security
        if not self.security.security_service_url:
            errors.append("SECURITY_URL is required")
        elif not self.security.security_service_url.startswith(('http://', 'https://')):
            errors.append("SECURITY_URL must be a valid HTTP/HTTPS URL")
        
        if self.security.jwt_secret_key and len(self.security.jwt_secret_key) < 32:
            warnings.append("JWT_SECRET_KEY should be at least 32 characters long for security")
        elif not self.security.jwt_secret_key:
            warnings.append("JWT_SECRET_KEY is not set - this may cause authentication issues")
        
        # Validate ranges
        if not (0 <= self.service.startup_delay <= 300):
            errors.append(f"SERVICE_STARTUP_DELAY must be between 0 and 300, got {self.service.startup_delay}")
        
        if not (1 <= self.rabbitmq.connection_retry_attempts <= 100):
            errors.append(f"RABBITMQ_CONNECTION_RETRY_ATTEMPTS must be between 1 and 100, got {self.rabbitmq.connection_retry_attempts}")
        
        if not (1 <= self.security.access_token_expire_minutes <= 1440):
            errors.append(f"ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440, got {self.security.access_token_expire_minutes}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'config_summary': {
                'environment': self.environment.value,
                'debug': self.debug,
                'log_level': self.log_level.value,
                'core_port': self.core_port,
                'database_name': self.database.name,
                'redis_host': self.redis.host,
                'rabbitmq_host': self.rabbitmq.host
            }
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT

class ConfigurationManager:
    """Manages configuration loading and validation"""
    
    def __init__(self):
        self._config: Optional[CoreConfig] = None
        self._validation_results: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> CoreConfig:
        """Load and validate configuration"""
        if self._config is None:
            logger.info("🔧 Loading configuration from environment...")
            self._config = CoreConfig.from_env()
            
            # Validate configuration
            self._validation_results = self._config.validate()
            
            if not self._validation_results['valid']:
                error_msg = "Configuration validation failed:\n" + "\n".join(self._validation_results['errors'])
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            # Log warnings
            for warning in self._validation_results['warnings']:
                logger.warning(f"⚠️ Configuration warning: {warning}")
            
            logger.info("✅ Configuration loaded and validated successfully")
            logger.info(f"Environment: {self._config.environment.value}")
            logger.info(f"Core port: {self._config.core_port}")
            logger.info(f"Log level: {self._config.log_level.value}")
        
        return self._config
    
    def get_config(self) -> CoreConfig:
        """Get current configuration (loads if not already loaded)"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def get_validation_results(self) -> Optional[Dict[str, Any]]:
        """Get configuration validation results"""
        return self._validation_results
    
    def reload_config(self) -> CoreConfig:
        """Reload configuration from environment"""
        self._config = None
        self._validation_results = None
        return self.load_config()

# Global configuration manager
config_manager = ConfigurationManager()

# Function to get the configuration manager instance
def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance"""
    return config_manager

# Convenience functions
def get_config() -> CoreConfig:
    """Get the current configuration"""
    return config_manager.get_config()

def validate_and_exit_on_failure():
    """Validate configuration and exit if invalid (for backward compatibility)"""
    try:
        config = config_manager.load_config()
        return config
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise SystemExit(1)

def get_validated_config() -> CoreConfig:
    """Get validated configuration (for backward compatibility)"""
    return config_manager.get_config()

# Export for backward compatibility
get_settings = get_config
