# Import auth utilities for backward compatibility
from .auth_utils import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    verify_access_token, verify_refresh_token, has_permission, require_permission,
    require_role, get_current_user, get_role_permissions, get_rate_limit_key,
    ROLES, security
)

__all__ = [
    'verify_password', 'get_password_hash', 'create_access_token', 'create_refresh_token',
    'verify_access_token', 'verify_refresh_token', 'has_permission', 'require_permission',
    'require_role', 'get_current_user', 'get_role_permissions', 'get_rate_limit_key',
    'ROLES', 'security'
]