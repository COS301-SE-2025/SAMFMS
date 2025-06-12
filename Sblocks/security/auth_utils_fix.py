def has_permission(permissions, required_permission):
    """Check if a user has a specific permission"""
    return required_permission in permissions
