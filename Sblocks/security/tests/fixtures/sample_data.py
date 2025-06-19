"""Test fixtures and sample data for testing."""
from datetime import datetime, timedelta


# Sample user data
SAMPLE_USERS = {
    "admin": {
        "user_id": "admin-123",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "password_hash": "$2b$12$hashed_admin_password",
        "is_active": True,
        "approved": True,
        "preferences": {
            "theme": "dark",
            "animations": "true",
            "email_alerts": "true",
            "push_notifications": "true",
            "two_factor": "true",
            "activity_log": "true",
            "session_timeout": "60 minutes"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    "fleet_manager": {
        "user_id": "manager-123",
        "email": "manager@example.com",
        "full_name": "Fleet Manager",
        "role": "fleet_manager",
        "password_hash": "$2b$12$hashed_manager_password",
        "is_active": True,
        "approved": True,
        "phoneNo": "+1234567890",
        "preferences": {
            "theme": "light",
            "animations": "true",
            "email_alerts": "true",
            "push_notifications": "true",
            "two_factor": "false",
            "activity_log": "true",
            "session_timeout": "30 minutes"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    "driver": {
        "user_id": "driver-123",
        "email": "driver@example.com",
        "full_name": "Test Driver",
        "role": "driver",
        "password_hash": "$2b$12$hashed_driver_password",
        "is_active": True,
        "approved": True,
        "phoneNo": "+1234567891",
        "preferences": {
            "theme": "light",
            "animations": "true",
            "email_alerts": "false",
            "push_notifications": "true",
            "two_factor": "false",
            "activity_log": "false",
            "session_timeout": "30 minutes"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
}

# Sample invitation data
SAMPLE_INVITATIONS = {
    "pending": {
        "invitation_id": "inv-123",
        "email": "invited@example.com",
        "full_name": "Invited User",
        "role": "driver",
        "phone_number": "+1234567892",
        "invited_by": "admin-123",
        "otp": "123456",
        "status": "pending",
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "created_at": datetime.utcnow()
    },
    "expired": {
        "invitation_id": "inv-456",
        "email": "expired@example.com",
        "full_name": "Expired User",
        "role": "fleet_manager",
        "invited_by": "admin-123",
        "otp": "789012",
        "status": "pending",
        "expires_at": datetime.utcnow() - timedelta(hours=1),
        "created_at": datetime.utcnow() - timedelta(days=1)
    }
}

# Sample audit log entries
SAMPLE_AUDIT_LOGS = [
    {
        "log_id": "log-123",
        "user_id": "admin-123",
        "action": "user_login",
        "details": {"ip_address": "192.168.1.1", "user_agent": "Test Browser"},
        "timestamp": datetime.utcnow()
    },
    {
        "log_id": "log-456",
        "user_id": "admin-123",
        "action": "user_created",
        "details": {"created_user_id": "driver-123", "role": "driver"},
        "timestamp": datetime.utcnow() - timedelta(minutes=30)
    },
    {
        "log_id": "log-789",
        "user_id": "driver-123",
        "action": "password_changed",
        "details": {"success": True},
        "timestamp": datetime.utcnow() - timedelta(hours=2)
    }
]

# Sample JWT tokens (for testing only)
SAMPLE_TOKENS = {
    "valid_admin": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbi0xMjMiLCJyb2xlIjoiYWRtaW4iLCJwZXJtaXNzaW9ucyI6WyIqIl0sImV4cCI6OTk5OTk5OTk5OX0.test",
    "valid_manager": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYW5hZ2VyLTEyMyIsInJvbGUiOiJmbGVldF9tYW5hZ2VyIiwiZXhwIjo5OTk5OTk5OTk5fQ.test",
    "valid_driver": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkcml2ZXItMTIzIiwicm9sZSI6ImRyaXZlciIsImV4cCI6OTk5OTk5OTk5OX0.test",
    "expired": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6MX0.test",
    "invalid": "invalid.token.here"
}

# Sample API request/response data
SAMPLE_API_DATA = {
    "login_request": {
        "email": "driver@example.com",
        "password": "TestPassword123!"
    },
    "signup_request": {
        "full_name": "New User",
        "email": "newuser@example.com",
        "password": "NewPassword123!",
        "role": "driver",
        "phoneNo": "+1234567893"
    },
    "create_user_request": {
        "full_name": "Manual User",
        "email": "manual@example.com",
        "role": "driver",
        "password": "ManualPassword123!",
        "phoneNo": "+1234567894"
    },
    "invitation_request": {
        "email": "invited@example.com",
        "full_name": "Invited User",
        "role": "fleet_manager",
        "phone_number": "+1234567895"
    },
    "update_permissions_request": {
        "user_id": "driver-123",
        "role": "fleet_manager"
    },
    "change_password_request": {
        "current_password": "OldPassword123!",
        "new_password": "NewPassword456!"
    },
    "update_profile_request": {
        "full_name": "Updated Name",
        "phoneNo": "+9876543210"
    },
    "update_preferences_request": {
        "preferences": {
            "theme": "dark",
            "animations": "false",
            "email_alerts": "true",
            "push_notifications": "false",
            "two_factor": "true",
            "activity_log": "true",
            "session_timeout": "45 minutes"
        }
    }
}

# Sample error responses
SAMPLE_ERRORS = {
    "invalid_credentials": {
        "status_code": 401,
        "detail": "Invalid credentials"
    },
    "user_not_found": {
        "status_code": 404,
        "detail": "User not found"
    },
    "access_denied": {
        "status_code": 403,
        "detail": "Access denied"
    },
    "validation_error": {
        "status_code": 422,
        "detail": "Validation error"
    },
    "duplicate_email": {
        "status_code": 400,
        "detail": "User with this email already exists"
    }
}
