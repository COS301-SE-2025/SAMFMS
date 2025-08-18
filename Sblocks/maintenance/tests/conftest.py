# maintenance/tests/conftest.py
import sys
import types
import pathlib
import pytest
from unittest.mock import patch
import enum

# -------------------------------------------------------------------
# 1) Paths (prefer /app so services resolve to /app/services;
#    also add /app/maintenance so api.* resolves)
# -------------------------------------------------------------------
TESTS_DIR = pathlib.Path(__file__).resolve().parent
APP_ROOT = pathlib.Path("/app")
MAINT_ROOT = APP_ROOT / "maintenance"

for p in (str(APP_ROOT), str(MAINT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# -------------------------------------------------------------------
# 2) Stub modules needed at import time (schemas, repos, utils, config, aio_pika)
# -------------------------------------------------------------------

# ----- schemas -------------------------------------------------------
schemas_pkg = types.ModuleType("schemas")

# schemas.responses — dict-like return that also supports .model_dump()
responses_mod = types.ModuleType("schemas.responses")

class _RBReturn(dict):
    def model_dump(self):
        return dict(self)

class ResponseBuilder:
    @staticmethod
    def success(**kwargs): return _RBReturn(**kwargs)
    @staticmethod
    def error(**kwargs):   return _RBReturn(**kwargs)

responses_mod.ResponseBuilder = ResponseBuilder

# schemas.requests — real Pydantic v2 models so FastAPI accepts them
requests_mod = types.ModuleType("schemas.requests")
from pydantic import BaseModel
try:
    from pydantic import ConfigDict
    class _CompatBaseModel(BaseModel):
        model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)
        def dict(self, *args, **kwargs):  # compatibility shim
            return self.model_dump(*args, **kwargs)
except Exception:
    class _CompatBaseModel(BaseModel):
        class Config:
            extra = "allow"
            arbitrary_types_allowed = True

class CreateMaintenanceRecordRequest(_CompatBaseModel): ...
class UpdateMaintenanceRecordRequest(_CompatBaseModel): ...
class MaintenanceQueryParams(_CompatBaseModel): ...
class CreateLicenseRecordRequest(_CompatBaseModel): ...
class UpdateLicenseRecordRequest(_CompatBaseModel): ...
class LicenseQueryParams(_CompatBaseModel): ...

for _cls in (
    CreateMaintenanceRecordRequest, UpdateMaintenanceRecordRequest, MaintenanceQueryParams,
    CreateLicenseRecordRequest, UpdateLicenseRecordRequest, LicenseQueryParams
):
    _cls.__module__ = "schemas.requests"

requests_mod.CreateMaintenanceRecordRequest = CreateMaintenanceRecordRequest
requests_mod.UpdateMaintenanceRecordRequest = UpdateMaintenanceRecordRequest
requests_mod.MaintenanceQueryParams = MaintenanceQueryParams
requests_mod.CreateLicenseRecordRequest = CreateLicenseRecordRequest
requests_mod.UpdateLicenseRecordRequest = UpdateLicenseRecordRequest
requests_mod.LicenseQueryParams = LicenseQueryParams

# schemas.entities — minimal enums/placeholders
entities_mod = types.ModuleType("schemas.entities")

class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class MaintenancePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MaintenanceRecord: ...
class LicenseRecord: ...
class LicenseType(str, enum.Enum):
    ROADWORTHY = "roadworthy"

entities_mod.MaintenanceStatus = MaintenanceStatus
entities_mod.MaintenancePriority = MaintenancePriority
entities_mod.MaintenanceRecord = MaintenanceRecord
entities_mod.LicenseRecord = LicenseRecord
entities_mod.LicenseType = LicenseType

# schemas.error_responses — used by request_consumer
error_responses_mod = types.ModuleType("schemas.error_responses")
class MaintenanceErrorBuilder:
    @staticmethod
    def internal_error(message: str, error_details: dict, correlation_id: str):
        return {"error": {"message": message, "details": error_details}, "correlation_id": correlation_id}
error_responses_mod.MaintenanceErrorBuilder = MaintenanceErrorBuilder

# register schemas
schemas_pkg.responses = responses_mod
schemas_pkg.requests = requests_mod
schemas_pkg.entities = entities_mod
schemas_pkg.error_responses = error_responses_mod
sys.modules["schemas"] = schemas_pkg
sys.modules["schemas.responses"] = responses_mod
sys.modules["schemas.requests"] = requests_mod
sys.modules["schemas.entities"] = entities_mod
sys.modules["schemas.error_responses"] = error_responses_mod

# ----- repositories (raise if not patched — catches forgotten mocks) --
repos_pkg = types.ModuleType("repositories")

def _nyi(*_a, **_k):
    raise NotImplementedError("This repository method must be patched in unit tests.")

class MaintenanceRecordsRepository:
    async def create(self, data): _nyi()
    async def get_by_id(self, _id): _nyi()
    async def update(self, _id, data): _nyi()
    async def delete(self, _id): _nyi()
    async def get_by_vehicle_id(self, vehicle_id, skip=0, limit=100): _nyi()
    async def get_by_status(self, status, skip=0, limit=100): _nyi()
    async def get_overdue_maintenance(self): _nyi()
    async def get_upcoming_maintenance(self, days_ahead): _nyi()
    async def get_maintenance_history(self, vehicle_id, start_dt=None, end_dt=None): _nyi()
    async def get_cost_summary(self, vehicle_id=None, start_date=None, end_date=None): _nyi()
    async def find(self, query=None, skip=0, limit=100, sort=None): _nyi()
    async def aggregate(self, pipeline): _nyi()
    async def count(self, query): _nyi()
    async def get_all_maintenance_records(self, skip=0, limit=100): _nyi()

class LicenseRecordsRepository:
    async def create(self, data): _nyi()
    async def get_by_id(self, _id): _nyi()
    async def update(self, _id, data): _nyi()
    async def delete(self, _id): _nyi()
    async def get_by_entity(self, entity_id, entity_type): _nyi()
    async def get_expiring_soon(self, days_ahead): _nyi()
    async def get_expired_licenses(self): _nyi()
    async def get_by_license_type(self, license_type): _nyi()
    async def find(self, query, skip=0, limit=100, sort=None): _nyi()
    async def count(self, query): _nyi()
    async def aggregate(self, pipeline): _nyi()

class MaintenanceVendorsRepository:
    async def get_active_vendors(self): _nyi()

class MaintenanceNotificationsRepository:
    async def create(self, data): _nyi()
    async def mark_as_sent(self, notification_id): _nyi()
    async def get_pending_notifications(self): _nyi()
    async def get_user_notifications(self, user_id, unread_only=False): _nyi()
    async def mark_as_read(self, notification_id): _nyi()

class MaintenanceSchedulesRepository:
    async def create_schedule(self, data): _nyi()
    async def get_schedule(self, schedule_id): _nyi()
    async def update_schedule(self, schedule_id, data): _nyi()
    async def delete_schedule(self, schedule_id): _nyi()
    async def find(self, query=None, skip=0, limit=100, sort=None): _nyi()

repos_pkg.MaintenanceRecordsRepository = MaintenanceRecordsRepository
repos_pkg.LicenseRecordsRepository = LicenseRecordsRepository
repos_pkg.MaintenanceVendorsRepository = MaintenanceVendorsRepository
repos_pkg.MaintenanceNotificationsRepository = MaintenanceNotificationsRepository
repos_pkg.MaintenanceSchedulesRepository = MaintenanceSchedulesRepository
sys.modules["repositories"] = repos_pkg

# ----- utils.vehicle_validator ---------------------------------------
utils_pkg = types.ModuleType("utils")
vehicle_validator_mod = types.ModuleType("utils.vehicle_validator")

class _VehicleValidator:
    async def validate_vehicle_id(self, vehicle_id: str) -> bool:
        return True  # default pass; tests can patch failures

vehicle_validator = _VehicleValidator()
vehicle_validator_mod.vehicle_validator = vehicle_validator
utils_pkg.vehicle_validator = vehicle_validator_mod
sys.modules["utils"] = utils_pkg
sys.modules["utils.vehicle_validator"] = vehicle_validator_mod

# ----- config.rabbitmq_config ----------------------------------------
cfg_pkg = types.ModuleType("config")
rabbit_cfg_mod = types.ModuleType("config.rabbitmq_config")

class RabbitMQConfig:
    CONNECTION_PARAMS = {"heartbeat": 60, "blocked_connection_timeout": 30}
    QUEUE_NAMES = {"maintenance": "maintenance.q"}
    EXCHANGE_NAMES = {"requests": "requests.ex", "responses": "responses.ex"}
    ROUTING_KEYS = {"core_responses": "core.responses"}
    REQUEST_TIMEOUTS = {"default_request_timeout": 25.0}
    def get_rabbitmq_url(self): return "amqp://guest:guest@localhost/"

def json_serializer(obj): return str(obj)

rabbit_cfg_mod.RabbitMQConfig = RabbitMQConfig
rabbit_cfg_mod.json_serializer = json_serializer
cfg_pkg.rabbitmq_config = rabbit_cfg_mod
sys.modules["config"] = cfg_pkg
sys.modules["config.rabbitmq_config"] = rabbit_cfg_mod

# ----- aio_pika + aio_pika.abc ---------------------------------------
aio_pika_mod = types.ModuleType("aio_pika")
aio_pika_abc_mod = types.ModuleType("aio_pika.abc")

class DeliveryMode:
    PERSISTENT = 2

class ExchangeType:
    DIRECT = "direct"

class Message:
    def __init__(self, body, delivery_mode=None, content_type=None, headers=None): ...

async def connect_robust(*args, **kwargs):
    class _Conn:
        is_closed = False
        async def channel(self):
            class _Chan:
                async def declare_exchange(self, *a, **k): return object()
                async def declare_queue(self, *a, **k):
                    class _Queue:
                        async def bind(self, *a, **k): ...
                        async def consume(self, *a, **k): ...
                    return _Queue()
            return _Chan()
        async def close(self): self.is_closed = True
    return _Conn()

aio_pika_mod.DeliveryMode = DeliveryMode
aio_pika_mod.ExchangeType = ExchangeType
aio_pika_mod.Message = Message
aio_pika_mod.connect_robust = connect_robust

class AbstractRobustConnection: ...
class AbstractRobustChannel: ...
class AbstractExchange: ...
class AbstractQueue: ...
class AbstractIncomingMessage: ...
class AbstractRobustExchange(AbstractExchange): ...
class AbstractRobustQueue(AbstractQueue): ...

aio_pika_abc_mod.AbstractRobustConnection = AbstractRobustConnection
aio_pika_abc_mod.AbstractRobustChannel = AbstractRobustChannel
aio_pika_abc_mod.AbstractExchange = AbstractExchange
aio_pika_abc_mod.AbstractQueue = AbstractQueue
aio_pika_abc_mod.AbstractIncomingMessage = AbstractIncomingMessage
aio_pika_abc_mod.AbstractRobustExchange = AbstractRobustExchange
aio_pika_abc_mod.AbstractRobustQueue = AbstractRobustQueue

sys.modules["aio_pika"] = aio_pika_mod
sys.modules["aio_pika.abc"] = aio_pika_abc_mod

# -------------------------------------------------------------------
# 3) A pytest-mock–like 'mocker' fixture that supports:
#    - mocker.patch("path", ...)
#    - mocker.patch.object(target, "attr", ...)
#    - mocker.object(target, "attr", ...)
#    All return STARTED patches (so they behave like pytest-mock).
# -------------------------------------------------------------------
class _PatchFacade:
    def __init__(self, owner):
        self._owner = owner
    def __call__(self, target, *args, **kwargs):
        return self._owner._start_patch(target, *args, **kwargs)
    def object(self, target, attribute, *args, **kwargs):
        return self._owner._start_patch_object(target, attribute, *args, **kwargs)

class _MockerFixture:
    def __init__(self):
        self._patchers = []
        self.patch = _PatchFacade(self)
    def _start_patch(self, target, *args, **kwargs):
        p = patch(target, *args, **kwargs)
        self._patchers.append(p)
        return p.start()
    def _start_patch_object(self, target, attribute, *args, **kwargs):
        p = patch.object(target, attribute, *args, **kwargs)
        self._patchers.append(p)
        return p.start()
    def object(self, target, attribute, *args, **kwargs):
        return self._start_patch_object(target, attribute, *args, **kwargs)
    def stopall(self):
        for p in reversed(self._patchers):
            try:
                p.stop()
            except Exception:
                pass
        self._patchers.clear()

@pytest.fixture
def mocker():
    mf = _MockerFixture()
    try:
        yield mf
    finally:
        mf.stopall()
        patch.stopall()
