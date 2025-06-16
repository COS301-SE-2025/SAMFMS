import os
from typing import Optional

class Settings:
    """Application settings and configuration"""
    
    # Database Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
    DATABASE_NAME: str = "security_db"
    
    # JWT Configuration
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Security Configuration
    LOGIN_ATTEMPT_LIMIT: int = int(os.getenv("LOGIN_ATTEMPT_LIMIT", "5"))
    
    # File Storage Configuration
    PROFILE_PICTURES_URL: str = os.getenv("PROFILE_PICTURES_URL", "/static/profile_pictures")
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_USERNAME: str = os.getenv("RABBITMQ_USERNAME", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # Role Configuration
    DEFAULT_FIRST_USER_ROLE: str = "admin"
    DEFAULT_USER_ROLE: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    
    @classmethod
    def validate_settings(cls):
        """Validate required settings"""
        if not cls.JWT_SECRET_KEY:
            if cls.ENVIRONMENT.lower() == "development":
                import secrets
                cls.JWT_SECRET_KEY = secrets.token_urlsafe(32)
                import logging
                logging.getLogger(__name__).warning("JWT_SECRET_KEY not set, using generated key for development")
            else:
                raise ValueError("JWT_SECRET_KEY must be set in environment variables for production")

settings = Settings()
settings.validate_settings()
