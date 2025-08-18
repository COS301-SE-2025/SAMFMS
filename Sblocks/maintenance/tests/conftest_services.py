# SAMFMS/Sblocks/maintenance/tests/unit/conftest_services.py
import sys, types
import asyncio
import pytest
from datetime import datetime

# --- Stub 'repositories' so service modules can import their repository classes ---
repos = types.ModuleType("repositories")

class _BaseRepo:
    # Each test will monkeypatch concrete methods as needed.
    def __init__(self, *a, **k): pass

# Analytics needs
class MaintenanceRecordsRepository(_BaseRepo): pass
class LicenseRecordsRepository(_BaseRepo): pass
class MaintenanceVendorsRepository(_BaseRepo): pass

# License service needs
class LicenseRecordsRepository(_BaseRepo): pass

# Maintenance services need
class MaintenanceSchedulesRepository(_BaseRepo): pass
class MaintenanceRecordsRepository(_BaseRepo): pass

# Notification service needs
class MaintenanceNotificationsRepository(_BaseRepo): pass

# Bind into module
for cls in [
    MaintenanceRecordsRepository, LicenseRecordsRepository, MaintenanceVendorsRepository,
    MaintenanceSchedulesRepository, MaintenanceNotificationsRepository
]:
    setattr(repos, cls.__name__, cls)

sys.modules["repositories"] = repos

# --- Stub 'utils.vehicle_validator.vehicle_validator' ---
utils = types.ModuleType("utils")
vv_mod = types.ModuleType("utils.vehicle_validator")

class _VehicleValidator:
    async def validate_vehicle_id(self, vehicle_id: str) -> bool:
        return True

vehicle_validator = _VehicleValidator()
vv_mod.vehicle_validator = vehicle_validator

sys.modules["utils"] = utils
sys.modules["utils.vehicle_validator"] = vv_mod

# --- Simple enums used by maintenance/notification services (strings keep it simple) ---
entities = sys.modules.get("schemas.entities")
if entities:
    # Provide defaults if not present
    if not hasattr(entities, "MaintenanceStatus"):
        class _MS:
            SCHEDULED = "scheduled"
            IN_PROGRESS = "in_progress"
            COMPLETED = "completed"
            OVERDUE = "overdue"
        entities.MaintenanceStatus = _MS

    if not hasattr(entities, "MaintenancePriority"):
        class _MP:
            LOW = "low"
            MEDIUM = "medium"
            HIGH = "high"
            CRITICAL = "critical"
        entities.MaintenancePriority = _MP

@pytest.fixture
def set_vehicle_validator(mocker):
    """Convenience fixture to flip vehicle existence on/off."""
    def _set(result: bool):
        async def _validate(_vid: str): return result
        mocker.patch("utils.vehicle_validator.vehicle_validator.validate_vehicle_id", _validate)
    return _set
