"""
Test configuration for SAMFMS integration tests
"""

import os
from typing import Dict, Any

# Test environment configuration
TEST_CONFIG = {
    "database": {
        "mongodb_url": os.getenv("TEST_MONGODB_URL", "mongodb://localhost:27017/samfms_test"),
        "database_name": "samfms_test",
        "max_connections": 10,
        "min_connections": 1,
        "max_idle_time": 30000,
        "socket_timeout": 30000,
        "connect_timeout": 30000,
        "server_selection_timeout": 30000,
        "heartbeat_frequency": 10000,
        "retry_writes": True,
        "retry_reads": True
    },
    "rabbitmq": {
        "host": os.getenv("TEST_RABBITMQ_HOST", "localhost"),
        "port": int(os.getenv("TEST_RABBITMQ_PORT", "5672")),
        "username": os.getenv("TEST_RABBITMQ_USERNAME", "guest"),
        "password": os.getenv("TEST_RABBITMQ_PASSWORD", "guest"),
        "virtual_host": os.getenv("TEST_RABBITMQ_VHOST", "/"),
        "exchange_name": "samfms_test_exchange",
        "routing_keys": {
            "vehicle_created": "vehicle.created",
            "vehicle_updated": "vehicle.updated",
            "driver_assigned": "driver.assigned",
            "maintenance_scheduled": "maintenance.scheduled",
            "maintenance_completed": "maintenance.completed"
        }
    },
    "services": {
        "core": {
            "host": os.getenv("TEST_CORE_HOST", "localhost"),
            "port": int(os.getenv("TEST_CORE_PORT", "8000")),
            "base_url": "http://localhost:8000"
        },
        "management": {
            "host": os.getenv("TEST_MANAGEMENT_HOST", "localhost"),
            "port": int(os.getenv("TEST_MANAGEMENT_PORT", "8001")),
            "base_url": "http://localhost:8001"
        },
        "maintenance": {
            "host": os.getenv("TEST_MAINTENANCE_HOST", "localhost"),
            "port": int(os.getenv("TEST_MAINTENANCE_PORT", "8002")),
            "base_url": "http://localhost:8002"
        },
        "security": {
            "host": os.getenv("TEST_SECURITY_HOST", "localhost"),
            "port": int(os.getenv("TEST_SECURITY_PORT", "8003")),
            "base_url": "http://localhost:8003"
        }
    },
    "auth": {
        "jwt_secret": os.getenv("TEST_JWT_SECRET", "test-jwt-secret-key"),
        "algorithm": "HS256",
        "access_token_expire_minutes": 30,
        "refresh_token_expire_days": 7
    },
    "test_data": {
        "test_user": {
            "email": "test@samfms.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "role": "admin"
        },
        "test_vehicle": {
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "registration_number": "TEST-123-GP",
            "vin": "1HGCM82633A123456",
            "color": "White",
            "fuel_type": "Petrol",
            "engine_size": "2.0L",
            "transmission": "Automatic",
            "status": "active"
        },
        "test_driver": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@samfms.com",
            "phone": "+27123456789",
            "license_number": "TEST-LICENSE-123",
            "license_expiry": "2025-12-31",
            "employee_id": "EMP-123",
            "status": "active"
        },
        "test_maintenance": {
            "maintenance_type": "oil_change",
            "description": "Regular oil change and filter replacement",
            "scheduled_date": "2024-01-15",
            "estimated_cost": 500.00,
            "service_provider": "Test Auto Service",
            "priority": "medium"
        }
    }
}

# Test environment variables for Docker Compose
DOCKER_COMPOSE_TEST_ENV = {
    "MONGODB_URL": TEST_CONFIG["database"]["mongodb_url"],
    "RABBITMQ_HOST": TEST_CONFIG["rabbitmq"]["host"],
    "RABBITMQ_PORT": str(TEST_CONFIG["rabbitmq"]["port"]),
    "RABBITMQ_USERNAME": TEST_CONFIG["rabbitmq"]["username"],
    "RABBITMQ_PASSWORD": TEST_CONFIG["rabbitmq"]["password"],
    "JWT_SECRET": TEST_CONFIG["auth"]["jwt_secret"],
    "ENVIRONMENT": "test"
}

# Test fixtures data
TEST_FIXTURES = {
    "vehicles": [
        {
            "id": "vehicle_001",
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "registration_number": "CAM-001-GP",
            "vin": "1HGCM82633A000001",
            "status": "active"
        },
        {
            "id": "vehicle_002",
            "make": "Honda",
            "model": "Civic",
            "year": 2022,
            "registration_number": "CIV-002-GP",
            "vin": "1HGCM82633A000002",
            "status": "active"
        },
        {
            "id": "vehicle_003",
            "make": "Ford",
            "model": "Focus",
            "year": 2021,
            "registration_number": "FOC-003-GP",
            "vin": "1HGCM82633A000003",
            "status": "maintenance"
        }
    ],
    "drivers": [
        {
            "id": "driver_001",
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@samfms.com",
            "license_number": "DL-001-GP",
            "status": "active"
        },
        {
            "id": "driver_002",
            "first_name": "Jane",
            "last_name": "Johnson",
            "email": "jane.johnson@samfms.com",
            "license_number": "DL-002-GP",
            "status": "active"
        },
        {
            "id": "driver_003",
            "first_name": "Bob",
            "last_name": "Williams",
            "email": "bob.williams@samfms.com",
            "license_number": "DL-003-GP",
            "status": "inactive"
        }
    ],
    "maintenance_records": [
        {
            "id": "maintenance_001",
            "vehicle_id": "vehicle_001",
            "maintenance_type": "oil_change",
            "description": "Regular oil change",
            "scheduled_date": "2024-01-15",
            "status": "scheduled"
        },
        {
            "id": "maintenance_002",
            "vehicle_id": "vehicle_002",
            "maintenance_type": "tire_replacement",
            "description": "Replace front tires",
            "scheduled_date": "2024-01-20",
            "status": "in_progress"
        },
        {
            "id": "maintenance_003",
            "vehicle_id": "vehicle_003",
            "maintenance_type": "brake_service",
            "description": "Brake pad replacement",
            "scheduled_date": "2024-01-10",
            "status": "completed"
        }
    ],
    "assignments": [
        {
            "id": "assignment_001",
            "vehicle_id": "vehicle_001",
            "driver_id": "driver_001",
            "start_date": "2024-01-15",
            "end_date": "2024-01-20",
            "purpose": "Security patrol",
            "status": "active"
        },
        {
            "id": "assignment_002",
            "vehicle_id": "vehicle_002",
            "driver_id": "driver_002",
            "start_date": "2024-01-16",
            "end_date": "2024-01-21",
            "purpose": "Transport duty",
            "status": "active"
        }
    ]
}

# Test API endpoints
TEST_ENDPOINTS = {
    "auth": {
        "login": "/auth/login",
        "logout": "/auth/logout",
        "refresh": "/auth/refresh",
        "register": "/auth/register"
    },
    "vehicles": {
        "list": "/api/vehicles",
        "create": "/api/vehicles",
        "get": "/api/vehicles/{id}",
        "update": "/api/vehicles/{id}",
        "delete": "/api/vehicles/{id}"
    },
    "drivers": {
        "list": "/api/drivers",
        "create": "/api/drivers",
        "get": "/api/drivers/{id}",
        "update": "/api/drivers/{id}",
        "delete": "/api/drivers/{id}"
    },
    "maintenance": {
        "records": "/maintenance/records",
        "schedules": "/maintenance/schedules",
        "analytics": "/maintenance/analytics"
    },
    "assignments": {
        "list": "/api/vehicle-assignments",
        "create": "/api/vehicle-assignments",
        "get": "/api/vehicle-assignments/{id}",
        "update": "/api/vehicle-assignments/{id}",
        "delete": "/api/vehicle-assignments/{id}"
    },
    "analytics": {
        "dashboard": "/api/analytics/dashboard",
        "vehicle_utilization": "/api/analytics/vehicle-utilization",
        "maintenance_costs": "/api/analytics/maintenance-costs"
    }
}

# Test database collections
TEST_COLLECTIONS = {
    "vehicles": "vehicles",
    "drivers": "drivers",
    "maintenance_records": "maintenance_records",
    "assignments": "assignments",
    "users": "users",
    "audit_logs": "audit_logs"
}

# Test timeouts and retries
TEST_TIMEOUTS = {
    "http_request": 30,
    "database_connection": 10,
    "rabbitmq_connection": 10,
    "service_startup": 60,
    "test_execution": 120
}

TEST_RETRIES = {
    "max_retries": 3,
    "retry_delay": 1.0,
    "backoff_factor": 2.0
}

# Test logging configuration
TEST_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "tests/logs/test_integration.log",
            "mode": "a"
        }
    },
    "loggers": {
        "test_integration": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}

# Test markers for pytest
TEST_MARKERS = {
    "unit": "Unit tests",
    "integration": "Integration tests",
    "e2e": "End-to-end tests",
    "slow": "Slow tests",
    "database": "Tests requiring database",
    "rabbitmq": "Tests requiring RabbitMQ",
    "auth": "Authentication tests",
    "api": "API tests",
    "service": "Service tests"
}

def get_test_config() -> Dict[str, Any]:
    """Get test configuration"""
    return TEST_CONFIG

def get_test_fixtures() -> Dict[str, Any]:
    """Get test fixtures"""
    return TEST_FIXTURES

def get_test_endpoints() -> Dict[str, Any]:
    """Get test API endpoints"""
    return TEST_ENDPOINTS

def get_docker_compose_env() -> Dict[str, str]:
    """Get Docker Compose environment variables for testing"""
    return DOCKER_COMPOSE_TEST_ENV

def get_test_config() -> Dict[str, Any]:
    """Get test configuration settings"""
    return TEST_CONFIG

def get_test_fixtures() -> Dict[str, Any]:
    """Get test fixtures and sample data"""
    return {
        "users": [
            {
                "id": "test_user_1",
                "username": "testuser1",
                "email": "test1@example.com",
                "role": "admin",
                "is_active": True
            }
        ],
        "vehicles": [
            {
                "id": "test_vehicle_1",
                "make": "Toyota",
                "model": "Camry",
                "year": 2022,
                "license_plate": "TEST001",
                "vin": "1HGBH41JXMN109186",
                "status": "active"
            }
        ],
        "drivers": [
            {
                "id": "test_driver_1",
                "name": "John Doe",
                "license_number": "DL123456789",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "status": "active"
            }
        ]
    }
