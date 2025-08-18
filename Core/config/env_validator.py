"""
Environment Variable Validation for SAMFMS Core Service
Validates required environment variables on startup
"""

import os
import logging
from typing import Dict, List, Optional, Any

try:
    # Pydantic v2 imports
    from pydantic import BaseModel, Field, field_validator
    from pydantic_settings import BaseSettings
    from pydantic import ValidationError
    PYDANTIC_V2 = True
except ImportError:
    try:
        # Pydantic v1 imports
        from pydantic import BaseSettings, Field, validator
        from pydantic.error_wrappers import ValidationError
        PYDANTIC_V2 = False
    except ImportError:
        # Fallback - create a simple configuration without validation
        print("Warning: Pydantic not available. Using simple configuration without validation.")
        BaseSettings = object
        Field = lambda default=None, **kwargs: default
        ValidationError = Exception
        PYDANTIC_V2 = False

logger = logging.getLogger(__name__)

class CoreServiceConfig(BaseSettings):
    """Core service configuration with validation"""
    
    # Service Configuration
    CORE_PORT: int = Field(default=8000, ge=1000, le=65535)
    ENVIRONMENT: str = Field(default="development", pattern="^(development|production|testing)$")
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    SERVICE_STARTUP_DELAY: int = Field(default=10, ge=0, le=300)
    
    # Database Configuration
    MONGODB_URL: str = Field(..., min_length=10)
    DATABASE_NAME: str = Field(default="samfms_core", min_length=1)
    
    # Message Queue Configuration
    RABBITMQ_URL: str = Field(..., min_length=10)
    RABBITMQ_CONNECTION_RETRY_ATTEMPTS: int = Field(default=30, ge=1, le=100)
    RABBITMQ_CONNECTION_RETRY_DELAY: int = Field(default=2, ge=1, le=60)
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="redis", min_length=1)
    REDIS_PORT: int = Field(default=6379, ge=1000, le=65535)
    
    # Security Configuration
    SECURITY_URL: str = Field(..., min_length=10)
    JWT_SECRET_KEY: Optional[str] = Field(None, min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=1440)
    
    if PYDANTIC_V2:
        @field_validator('JWT_SECRET_KEY')
        @classmethod
        def validate_jwt_secret(cls, v):
            if v and len(v) < 32:
                raise ValueError('JWT_SECRET_KEY must be at least 32 characters long')
            return v
        
        @field_validator('MONGODB_URL')
        @classmethod
        def validate_mongodb_url(cls, v):
            if not v.startswith(('mongodb://', 'mongodb+srv://')):
                raise ValueError('MONGODB_URL must be a valid MongoDB connection string')
            return v
        
        @field_validator('RABBITMQ_URL')
        @classmethod
        def validate_rabbitmq_url(cls, v):
            if not v.startswith('amqp://'):
                raise ValueError('RABBITMQ_URL must be a valid AMQP connection string')
            return v
        
        @field_validator('SECURITY_URL')
        @classmethod
        def validate_security_url(cls, v):
            if not v.startswith(('http://', 'https://')):
                raise ValueError('SECURITY_URL must be a valid HTTP/HTTPS URL')
            return v
    else:
        @validator('JWT_SECRET_KEY')
        def validate_jwt_secret(cls, v):
            if v and len(v) < 32:
                raise ValueError('JWT_SECRET_KEY must be at least 32 characters long')
            return v
        
        @validator('MONGODB_URL')
        def validate_mongodb_url(cls, v):
            if not v.startswith(('mongodb://', 'mongodb+srv://')):
                raise ValueError('MONGODB_URL must be a valid MongoDB connection string')
            return v
        
        @validator('RABBITMQ_URL')
        def validate_rabbitmq_url(cls, v):
            if not v.startswith('amqp://'):
                raise ValueError('RABBITMQ_URL must be a valid AMQP connection string')
            return v
        
        @validator('SECURITY_URL')
        def validate_security_url(cls, v):
            if not v.startswith(('http://', 'https://')):
                raise ValueError('SECURITY_URL must be a valid HTTP/HTTPS URL')
            return v

    class Config:
        env_file = ".env"
        case_sensitive = True

class FrontendConfig(BaseSettings):
    """Frontend configuration validation"""
    
    REACT_APP_CORE_PORT: int = Field(default=21004, ge=1000, le=65535)
    REACT_APP_API_BASE_URL: Optional[str] = Field(None)
    REACT_APP_DOMAIN: Optional[str] = Field(None)
    FRONTEND_PORT: int = Field(default=21015, ge=1000, le=65535)
    CHOKIDAR_USEPOLLING: bool = Field(default=False)
    
    if PYDANTIC_V2:
        @field_validator('REACT_APP_API_BASE_URL')
        @classmethod
        def validate_api_base_url(cls, v):
            if v and not v.startswith(('http://', 'https://')):
                raise ValueError('REACT_APP_API_BASE_URL must be a valid HTTP/HTTPS URL')
            return v
    else:
        @validator('REACT_APP_API_BASE_URL')
        def validate_api_base_url(cls, v):
            if v and not v.startswith(('http://', 'https://')):
                raise ValueError('REACT_APP_API_BASE_URL must be a valid HTTP/HTTPS URL')
            return v

    class Config:
        env_file = ".env"
        case_sensitive = True

def validate_environment() -> Dict[str, Any]:
    """
    Validate all environment variables and return configuration
    
    Returns:
        Dict containing validated configuration
        
    Raises:
        SystemExit: If validation fails
    """
    validation_results = {
        "core_config": None,
        "frontend_config": None,
        "errors": [],
        "warnings": [],
        "valid": True
    }
    
    try:
        # Validate Core service configuration
        core_config = CoreServiceConfig()
        validation_results["core_config"] = core_config.dict()
        logger.info("✅ Core service configuration validated successfully")
        
    except ValidationError as e:
        validation_results["valid"] = False
        validation_results["errors"].extend([
            f"Core config error: {error['loc'][0]} - {error['msg']}" 
            for error in e.errors()
        ])
        logger.error("❌ Core service configuration validation failed")
        
    try:
        # Validate Frontend configuration
        frontend_config = FrontendConfig()
        validation_results["frontend_config"] = frontend_config.dict()
        logger.info("✅ Frontend configuration validated successfully")
        
    except ValidationError as e:
        validation_results["valid"] = False
        validation_results["errors"].extend([
            f"Frontend config error: {error['loc'][0]} - {error['msg']}" 
            for error in e.errors()
        ])
        logger.error("❌ Frontend configuration validation failed")
    
    # Check for critical missing variables
    critical_vars = [
        'JWT_SECRET_KEY',
        'MONGODB_URL',
        'RABBITMQ_URL',
        'SECURITY_URL'
    ]
    
    missing_critical = []
    for var in critical_vars:
        if not os.getenv(var):
            missing_critical.append(var)
    
    if missing_critical:
        validation_results["valid"] = False
        validation_results["errors"].append(
            f"Missing critical environment variables: {', '.join(missing_critical)}"
        )
    
    # Port conflict detection
    used_ports = []
    port_vars = [
        ('CORE_PORT', os.getenv('CORE_PORT', '21004')),
        ('FRONTEND_PORT', os.getenv('FRONTEND_PORT', '21015')),
        ('RABBITMQ_PORT', os.getenv('RABBITMQ_PORT', '21000')),
        ('MONGODB_PORT', os.getenv('MONGODB_PORT', '21003')),
        ('REDIS_EXTERNAL_PORT', os.getenv('REDIS_EXTERNAL_PORT', '21002'))
    ]
    
    for var_name, port_str in port_vars:
        try:
            port = int(port_str)
            if port in used_ports:
                validation_results["warnings"].append(f"Port conflict detected: {port} used by multiple services")
            used_ports.append(port)
        except ValueError:
            validation_results["errors"].append(f"Invalid port value for {var_name}: {port_str}")
    
    return validation_results

def validate_and_exit_on_failure():
    """Validate environment and exit if validation fails"""
    results = validate_environment()
    
    if results["errors"]:
        logger.error("❌ Environment validation failed:")
        for error in results["errors"]:
            logger.error(f"  - {error}")
        raise SystemExit(1)
    
    if results["warnings"]:
        logger.warning("⚠️  Environment validation warnings:")
        for warning in results["warnings"]:
            logger.warning(f"  - {warning}")
    
    logger.info("✅ Environment validation completed successfully")
    return results

def get_validated_config() -> CoreServiceConfig:
    """Get validated core service configuration"""
    try:
        return CoreServiceConfig()
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    # Run validation as standalone script
    import sys
    logging.basicConfig(level=logging.INFO)
    
    results = validate_environment()
    
    print("\n=== SAMFMS Environment Validation Report ===")
    print(f"Valid: {'✅ Yes' if results['valid'] else '❌ No'}")
    
    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  ❌ {error}")
    
    if results["warnings"]:
        print("\nWarnings:")
        for warning in results["warnings"]:
            print(f"  ⚠️  {warning}")
    
    if results["core_config"]:
        print(f"\nCore Service Port: {results['core_config']['CORE_PORT']}")
        print(f"Environment: {results['core_config']['ENVIRONMENT']}")
        print(f"Log Level: {results['core_config']['LOG_LEVEL']}")
    
    sys.exit(0 if results["valid"] else 1)
