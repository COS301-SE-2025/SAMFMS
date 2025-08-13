# /app/tests/conftest.py
import sys
import types
import pathlib
import pytest
from unittest.mock import patch
from types import SimpleNamespace

# ------- 1) Put the maintenance package on sys.path (dynamic search) -------
# We look for the maintenance "api/dependencies.py" file anywhere under the repo root.
TESTS_DIR = pathlib.Path(__file__).resolve().parent           # /app/tests
REPO_ROOT = TESTS_DIR.parent                                  # /app
api_candidates = list(REPO_ROOT.rglob("api/dependencies.py"))

if not api_candidates:
    # As a fallback, try common layouts (SBLOCKS vs Sblocks)
    common = [
        REPO_ROOT / "SAMFMS" / "SBLOCKS" / "maintenance" / "api" / "dependencies.py",
        REPO_ROOT / "SAMFMS" / "Sblocks" / "maintenance" / "api" / "dependencies.py",
        REPO_ROOT / "SBLOCKS" / "maintenance" / "api" / "dependencies.py",
        REPO_ROOT / "maintenance" / "api" / "dependencies.py",
    ]
    for p in common:
        if p.exists():
            api_candidates = [p]
            break

if api_candidates:
    # maintenance dir is two up from api/dependencies.py (…/maintenance)
    MAINT_DIR = api_candidates[0].parent.parent
    if str(MAINT_DIR) not in sys.path:
        sys.path.insert(0, str(MAINT_DIR))

# ------- 2) Stub 'schemas' package so imports don't explode -------
schemas_pkg = types.ModuleType("schemas")

responses_mod = types.ModuleType("schemas.responses")

class _RBReturn:
    """Default object mimicking pydantic response with .model_dump()."""
    def __init__(self, **payload):
        self._payload = payload
    def model_dump(self):
        return self._payload

class ResponseBuilder:
    @staticmethod
    def success(**kwargs):
        return _RBReturn(**kwargs)
    @staticmethod
    def error(**kwargs):
        return _RBReturn(**kwargs)

responses_mod.ResponseBuilder = ResponseBuilder

requests_mod = types.ModuleType("schemas.requests")
# Minimal classes so "from schemas.requests import X" works
class CreateMaintenanceRecordRequest: ...
class UpdateMaintenanceRecordRequest: ...
class MaintenanceQueryParams: ...
class CreateLicenseRecordRequest: ...
class UpdateLicenseRecordRequest: ...
class LicenseQueryParams: ...
for cls in [
    CreateMaintenanceRecordRequest, UpdateMaintenanceRecordRequest, MaintenanceQueryParams,
    CreateLicenseRecordRequest, UpdateLicenseRecordRequest, LicenseQueryParams,
]:
    setattr(requests_mod, cls.__name__, cls)

entities_mod = types.ModuleType("schemas.entities")

schemas_pkg.responses = responses_mod
schemas_pkg.requests = requests_mod
schemas_pkg.entities = entities_mod
sys.modules["schemas"] = schemas_pkg
sys.modules["schemas.responses"] = responses_mod
sys.modules["schemas.requests"] = requests_mod
sys.modules["schemas.entities"] = entities_mod

# ------- 3) Stub 'services' package with the singletons routes import -------
services_pkg = types.ModuleType("services")

notif_mod = types.ModuleType("services.notification_service")
class _NotificationService:
    async def get_pending_notifications(self): ...
    async def get_user_notifications(self, user_id, unread_only): ...
    async def process_pending_notifications(self): ...
    async def mark_notification_read(self, notification_id): ...
    async def send_notification(self, notification_id): ...
notif_mod.notification_service = _NotificationService()

analytics_mod = types.ModuleType("services.analytics_service")
class _MaintenanceAnalyticsService:
    async def get_maintenance_dashboard(self): ...
    async def get_cost_analytics(self, *, vehicle_id=None, start_date=None, end_date=None, group_by=None): ...
    async def get_maintenance_trends(self, days): ...
    async def get_vendor_analytics(self): ...
    async def get_license_analytics(self): ...
analytics_mod.maintenance_analytics_service = _MaintenanceAnalyticsService()

license_mod = types.ModuleType("services.license_service")
class _LicenseService:
    async def create_license_record(self, data): ...
    async def search_licenses(self, *, query, skip, limit, sort_by, sort_order): ...
    async def get_total_count(self, query): ...
    async def get_license_summary(self, *args, **kwargs): ...
    async def get_license_record(self, record_id): ...
    async def update_license_record(self, record_id, data): ...
    async def delete_license_record(self, record_id): ...
    async def get_entity_licenses(self, entity_id, entity_type): ...
    async def get_expiring_licenses(self, days): ...
    async def get_expired_licenses(self): ...
    async def get_licenses_by_type(self, license_type): ...
    async def renew_license(self, record_id, new_date, renewal_cost): ...
    async def deactivate_license(self, record_id): ...
license_mod.license_service = _LicenseService()

maint_mod = types.ModuleType("services.maintenance_service")
class _MaintenanceRecordsService:
    async def create_maintenance_record(self, data): ...
    async def search_maintenance_records(self, *, query, pagination): ...
    async def search_maintenance_records_text(self, q, pagination): ...
    async def get_maintenance_record_by_id(self, record_id): ...
    async def update_maintenance_record(self, record_id, data, updated_by): ...
    async def delete_maintenance_record(self, record_id, user_id): ...
maint_mod.maintenance_records_service = _MaintenanceRecordsService()

services_pkg.notification_service = notif_mod
services_pkg.analytics_service = analytics_mod
services_pkg.license_service = license_mod
services_pkg.maintenance_service = maint_mod

sys.modules["services"] = services_pkg
sys.modules["services.notification_service"] = notif_mod
sys.modules["services.analytics_service"] = analytics_mod
sys.modules["services.license_service"] = license_mod
sys.modules["services.maintenance_service"] = maint_mod

# ------- 4) Provide a 'mocker' fixture if pytest-mock isn't installed -------
class _PatchWrapper:
    def __call__(self, target, *args, **kwargs):
        return patch(target, *args, **kwargs).start()
    def object(self, target, attribute, *args, **kwargs):
        return patch.object(target, attribute, *args, **kwargs).start()

@pytest.fixture
def mocker():
    wrapper = _PatchWrapper()
    obj = SimpleNamespace(patch=wrapper)
    yield obj
    patch.stopall()
