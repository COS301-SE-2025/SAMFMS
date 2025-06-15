# Backward compatibility - redirect to new structure
# This file provides backward compatibility for existing imports

from utils.auth_utils import (
    pwd_context, security, ROLES, verify_password, get_password_hash,
    create_access_token, create_refresh_token, verify_access_token,
    verify_refresh_token, has_permission, require_permission, require_role,
    get_current_user, get_role_permissions, get_rate_limit_key
)
from config.settings import settings

# Re-export constants for backward compatibility
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
LOGIN_ATTEMPT_LIMIT = settings.LOGIN_ATTEMPT_LIMIT
DEFAULT_FIRST_USER_ROLE = settings.DEFAULT_FIRST_USER_ROLE
DEFAULT_USER_ROLE = settings.DEFAULT_USER_ROLE

# Keep all exports for backward compatibility
__all__ = [
    "pwd_context", "security", "ROLES", "SECRET_KEY", "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS",
    "LOGIN_ATTEMPT_LIMIT", "DEFAULT_FIRST_USER_ROLE", "DEFAULT_USER_ROLE",
    "verify_password", "get_password_hash", "create_access_token",
    "create_refresh_token", "verify_access_token", "verify_refresh_token",
    "has_permission", "require_permission", "require_role",
    "get_current_user", "get_role_permissions", "get_rate_limit_key"
]
