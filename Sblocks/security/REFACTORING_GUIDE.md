# Security Service - Refactored Structure Migration Guide

## Overview

The security service has been refactored into a cleaner, more maintainable architecture while maintaining backward compatibility with the Core service.

## New Structure

```
security/
├── config/
│   ├── __init__.py
│   ├── settings.py          # Centralized configuration
│   └── database.py          # Database connection and basic operations
├── models/
│   ├── __init__.py
│   ├── api_models.py        # API request/response models
│   └── database_models.py   # Database models and message queue models
├── repositories/
│   ├── __init__.py
│   ├── user_repository.py   # User data operations
│   └── audit_repository.py  # Audit and security logging operations
├── services/
│   ├── __init__.py
│   ├── auth_service.py      # Authentication business logic
│   └── user_service.py      # User management business logic
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py       # Authentication endpoints
│   ├── user_routes.py       # User management endpoints
│   └── admin_routes.py      # Admin-specific endpoints
├── middleware/
│   ├── __init__.py
│   ├── logging_middleware.py    # Request logging
│   └── security_middleware.py   # Security headers and CORS
├── utils/
│   ├── __init__.py
│   └── auth_utils.py        # Authentication utilities
├── legacy_imports.py        # Backward compatibility layer
├── main_new.py             # New main application file
└── main.py                 # Original main (kept for compatibility)
```

## Key Improvements

### 1. Separation of Concerns

- **Repositories**: Data access layer
- **Services**: Business logic layer
- **Routes**: API endpoints layer
- **Models**: Data models separated by purpose
- **Config**: Centralized configuration

### 2. Maintainability

- Smaller, focused files
- Clear dependencies
- Easier testing
- Better error handling

### 3. Backward Compatibility

- `legacy_imports.py` provides compatibility layer
- Existing Core integration continues to work
- Gradual migration path available

## Migration Steps

### Phase 1: Verify Compatibility (Current)

1. New structure created alongside existing files
2. `legacy_imports.py` maintains compatibility
3. Core service continues to work unchanged

### Phase 2: Testing (Next)

1. Test all endpoints with new structure
2. Verify Core service integration
3. Performance testing

### Phase 3: Deployment (Future)

1. Replace `main.py` with `main_new.py`
2. Update imports to use new structure
3. Remove old files

## Core Service Compatibility

The Core service can continue using existing imports:

```python
from Sblocks.security.models import SecurityUser, TokenResponse
from Sblocks.security.auth_utils import verify_access_token
from Sblocks.security.database import security_users_collection
```

These imports will be automatically redirected to the new structure via `legacy_imports.py`.

## Benefits for Core Service

1. **No Immediate Changes Required**: Continue using existing imports
2. **Improved Reliability**: Better error handling and logging
3. **Enhanced Security**: Improved token management and validation
4. **Better Performance**: Optimized database queries and caching
5. **Future-Proof**: Easier to extend and maintain

## Configuration

The new structure uses environment variables for configuration:

- `JWT_SECRET_KEY`: JWT secret key (required in production)
- `MONGODB_URL`: MongoDB connection string
- `REDIS_HOST`: Redis host
- `RABBITMQ_HOST`: RabbitMQ host
- `LOGIN_ATTEMPT_LIMIT`: Failed login attempt limit

## Testing

To test the new structure:

1. Run the service with `main_new.py`
2. Verify all endpoints work correctly
3. Test Core service integration
4. Check logging and monitoring

## Rollback Plan

If issues arise:

1. Revert to original `main.py`
2. Original structure remains intact
3. No data loss or corruption
4. Immediate fallback available
