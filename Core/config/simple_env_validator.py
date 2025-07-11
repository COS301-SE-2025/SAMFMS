"""
Simple Environment Variable Validation for SAMFMS Core Service
Validates required environment variables on startup without external dependencies
"""

import os
import logging
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class SimpleConfig:
    """Simple configuration class without Pydantic dependency"""
    
    def __init__(self):
        # Load environment variables with defaults
        self.CORE_PORT = int(os.getenv('CORE_PORT', '8000'))
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.SERVICE_STARTUP_DELAY = int(os.getenv('SERVICE_STARTUP_DELAY', '10'))
        
        # Database Configuration
        self.MONGODB_URL = os.getenv('MONGODB_URL', '')
        self.DATABASE_NAME = os.getenv('DATABASE_NAME', 'samfms_core')
        
        # Message Queue Configuration
        self.RABBITMQ_URL = os.getenv('RABBITMQ_URL', '')
        self.RABBITMQ_CONNECTION_RETRY_ATTEMPTS = int(os.getenv('RABBITMQ_CONNECTION_RETRY_ATTEMPTS', '30'))
        self.RABBITMQ_CONNECTION_RETRY_DELAY = int(os.getenv('RABBITMQ_CONNECTION_RETRY_DELAY', '2'))
        
        # Redis Configuration
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
        
        # Security Configuration
        self.SECURITY_URL = os.getenv('SECURITY_URL', '')
        self.JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return results"""
        errors = []
        warnings = []
        
        # Validate ports
        if not (1000 <= self.CORE_PORT <= 65535):
            errors.append(f"CORE_PORT must be between 1000 and 65535, got {self.CORE_PORT}")
        
        if not (1000 <= self.REDIS_PORT <= 65535):
            errors.append(f"REDIS_PORT must be between 1000 and 65535, got {self.REDIS_PORT}")
        
        # Validate environment
        if self.ENVIRONMENT not in ['development', 'production', 'testing']:
            errors.append(f"ENVIRONMENT must be one of: development, production, testing, got {self.ENVIRONMENT}")
        
        # Validate log level
        if self.LOG_LEVEL not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append(f"LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL, got {self.LOG_LEVEL}")
        
        # Validate required URLs
        if not self.MONGODB_URL:
            errors.append("MONGODB_URL is required")
        elif not self.MONGODB_URL.startswith(('mongodb://', 'mongodb+srv://')):
            errors.append("MONGODB_URL must be a valid MongoDB connection string")
        
        if not self.RABBITMQ_URL:
            errors.append("RABBITMQ_URL is required")
        elif not self.RABBITMQ_URL.startswith('amqp://'):
            errors.append("RABBITMQ_URL must be a valid AMQP connection string")
        
        if not self.SECURITY_URL:
            errors.append("SECURITY_URL is required")
        elif not self.SECURITY_URL.startswith(('http://', 'https://')):
            errors.append("SECURITY_URL must be a valid HTTP/HTTPS URL")
        
        # Validate JWT secret
        if self.JWT_SECRET_KEY and len(self.JWT_SECRET_KEY) < 32:
            warnings.append("JWT_SECRET_KEY should be at least 32 characters long for security")
        elif not self.JWT_SECRET_KEY:
            warnings.append("JWT_SECRET_KEY is not set - this may cause authentication issues")
        
        # Validate ranges
        if not (0 <= self.SERVICE_STARTUP_DELAY <= 300):
            errors.append(f"SERVICE_STARTUP_DELAY must be between 0 and 300, got {self.SERVICE_STARTUP_DELAY}")
        
        if not (1 <= self.RABBITMQ_CONNECTION_RETRY_ATTEMPTS <= 100):
            errors.append(f"RABBITMQ_CONNECTION_RETRY_ATTEMPTS must be between 1 and 100, got {self.RABBITMQ_CONNECTION_RETRY_ATTEMPTS}")
        
        if not (1 <= self.RABBITMQ_CONNECTION_RETRY_DELAY <= 60):
            errors.append(f"RABBITMQ_CONNECTION_RETRY_DELAY must be between 1 and 60, got {self.RABBITMQ_CONNECTION_RETRY_DELAY}")
        
        if not (1 <= self.ACCESS_TOKEN_EXPIRE_MINUTES <= 1440):
            errors.append(f"ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440, got {self.ACCESS_TOKEN_EXPIRE_MINUTES}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'config': self.__dict__
        }

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
        "errors": [],
        "warnings": [],
        "valid": True
    }
    
    try:
        # Validate Core service configuration
        core_config = SimpleConfig()
        core_validation = core_config.validate()
        
        validation_results["core_config"] = core_validation['config']
        validation_results["errors"] = core_validation['errors']
        validation_results["warnings"] = core_validation['warnings']
        validation_results["valid"] = core_validation['valid']
        
        if core_validation['valid']:
            logger.info("✅ Core service configuration validated successfully")
        else:
            logger.error("❌ Core service configuration validation failed")
        
    except Exception as e:
        validation_results["valid"] = False
        validation_results["errors"].append(f"Configuration error: {str(e)}")
        logger.error(f"❌ Configuration validation exception: {e}")
    
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

def get_validated_config():
    """Get validated core service configuration"""
    try:
        config = SimpleConfig()
        validation = config.validate()
        if not validation['valid']:
            logger.error(f"Configuration validation failed: {validation['errors']}")
            raise SystemExit(1)
        return config
    except Exception as e:
        logger.error(f"Configuration error: {e}")
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
