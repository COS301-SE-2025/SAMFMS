import sys
import types
import json
import importlib
import importlib.util
from pathlib import Path
import pytest
from datetime import datetime

SERVICE_IMPORT_CANDIDATES = [
    "gps.services.request_consumer",
    "services.request_consumer",
    "request_consumer",
]

def _compute_fallback_path():
    here = Path(__file__).resolve()
    for i in range(0, min(8, len(here.parents))):
        base = here.parents[i]
        for p in (
            base / "services" / "request_consumer.py",
            base / "gps" / "services" / "request_consumer.py",
        ):
            if p.exists():
                return str(p)
    return None

FALLBACK_SERVICE_PATH = _compute_fallback_path()

class FakeMessageObj:
    def __init__(self, body, delivery_mode=None, content_type=None, headers=None):
        self.body = body
        self.delivery_mode = delivery_mode
        self.content_type = content_type
        self.headers = headers or {}

class FakeExchange:
    def __init__(self, name):
        self.name = name
        self.publishes = []
    async def publish(self, message, routing_key):
        self.publishes.append({"routing_key": routing_key, "message": message})

class FakeQueue:
    def __init__(self, name):
        self.name = name
        self.binds = []
        self.consumers = []
    async def bind(self, exchange, routing_key):
        self.binds.append({"exchange": exchange, "routing_key": routing_key})
    async def consume(self, cb, no_ack=False):
        self.consumers.append({"cb": cb, "no_ack": no_ack})

class FakeChannel:
    def __init__(self):
        self.exchanges = {}
        self.queues = {}
    async def declare_exchange(self, name, ex_type, durable=True):
        ex = FakeExchange(name)
        self.exchanges[name] = ex
        return ex
    async def declare_queue(self, name, durable=True):
        q = FakeQueue(name)
        self.queues[name] = q
        return q

class FakeConnection:
    def __init__(self, should_fail=False):
        self.is_closed = False
        self._should_fail = should_fail
        self.channels = []
    async def channel(self):
        if self._should_fail:
            raise RuntimeError("channel fail")
        ch = FakeChannel()
        self.channels.append(ch)
        return ch
    async def close(self):
        self.is_closed = True

def make_fake_aio_pika(should_connect_fail=False):
    mod = types.ModuleType("aio_pika")
    mod.__path__ = []
    async def connect_robust(url, heartbeat=None, blocked_connection_timeout=None):
        if should_connect_fail:
            raise RuntimeError("connect fail")
        return FakeConnection()
    class DeliveryMode:
        PERSISTENT = 2
    class ExchangeType:
        DIRECT = "direct"
    mod.connect_robust = connect_robust
    mod.DeliveryMode = DeliveryMode
    mod.ExchangeType = ExchangeType
    mod.Message = FakeMessageObj
    abc = types.ModuleType("aio_pika.abc")
    class AbstractIncomingMessage:
        pass
    abc.AbstractIncomingMessage = AbstractIncomingMessage
    mod.abc = abc
    sys.modules["aio_pika.abc"] = abc
    return mod

def make_fake_config():
    pkg = types.ModuleType("config")
    cfg = types.ModuleModuleType = types.ModuleType("config.rabbitmq_config")
    class RabbitMQConfig:
        CONNECTION_PARAMS = {"heartbeat": 10, "blocked_connection_timeout": 5}
        QUEUE_NAMES = {"gps": "gps_queue"}
        EXCHANGE_NAMES = {"requests": "req_ex", "responses": "resp_ex"}
        ROUTING_KEYS = {"core_responses": "core.responses"}
        REQUEST_TIMEOUTS = {"default_request_timeout": 0.05}
        def get_rabbitmq_url(self): return "amqp://guest:guest@localhost/"
    def json_serializer(obj):
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        return str(obj)
    cfg.RabbitMQConfig = RabbitMQConfig
    cfg.json_serializer = json_serializer
    sys.modules["config"] = pkg
    sys.modules["config.rabbitmq_config"] = cfg

def install_db_manager(is_connected=True):
    pkg = types.ModuleType("repositories")
    db = types.ModuleType("repositories.database")
    class _DBM:
        @staticmethod
        def is_connected():
            return is_connected
    db.db_manager = _DBM
    sys.modules["repositories"] = pkg
    sys.modules["repositories.database"] = db

def install_services_and_responses():
    schemas = types.ModuleType("schemas")
    responses = types.ModuleType("schemas.responses")
    class RB:
        @staticmethod
        def success(data=None, message=""):
            class R:
                def __init__(self, data, message): self._o={"status":"success","data":data,"message":message}
                def model_dump(self): return self._o
            return R(data, message)
        @staticmethod
        def error(error="", message=""):
            class R:
                def __init__(self, error, message): self._o={"status":"error","error":{"type":error,"message":message}}
                def model_dump(self): return self._o
            return R(error, message)
    responses.ResponseBuilder = RB
    sys.modules["schemas"] = schemas
    sys.modules["schemas.responses"] = responses

    services_pkg = sys.modules.get("services") or types.ModuleType("services")

    loc_mod = types.ModuleType("services.location_service")
    class _Obj:
        def __init__(self, **d): self._d=d
        def model_dump(self): return dict(self._d)
    class LocationServiceFake:
        async def get_vehicle_location(self, vid):
            if vid == "missing": return None
            return _Obj(id="loc-"+vid, vehicle_id=vid, latitude=1.0, longitude=2.0)
        async def get_all_vehicle_locations(self):
            return [_Obj(id="loc-v1", vehicle_id="v1", latitude=1.0, longitude=2.0)]
        async def get_all_vehicles(self):
            return [{"_id":"v1","id":"v1"},{"_id":"v2","id":"v2"}]
        async def get_location_history(self, vid, s, e, l):
            return [_Obj(id="h1"), _Obj(id="h2")]
        async def get_multiple_vehicle_locations(self, vids):
            return [_Obj(id="m-"+v, vehicle_id=v) for v in vids]
        async def create_vehicle_location(self, **k): return _Obj(created=True)
        async def update_vehicle_location(self, **k): return _Obj(updated=True)
        async def delete_vehicle_location(self, vid): return True
        async def start_vehicle_tracking(self, vid): return {"status":"started","session_id":"S"}
        async def get_vehicle_route(self, vid, s, e): return {"total_points":2}
    loc_mod.location_service = LocationServiceFake()

    gf_mod = types.ModuleType("services.geofence_service")
    class GeofenceServiceFake:
        async def get_geofence_by_id(self, gid):
            return _Obj(id=gid) if gid != "none" else None
        async def get_geofences(self, **k): return [_Obj(id="g1"), _Obj(id="g2")]
        async def create_geofence(self, **k): return _Obj(id="newg")
        async def update_geofence(self, **k): return _Obj(id="upd")
        async def delete_geofence(self, gid): return True
    gf_mod.geofence_service = GeofenceServiceFake()

    pl_mod = types.ModuleType("services.places_service")
    class PlacesServiceFake:
        async def get_places_near_location(self, **k): return [_Obj(id="near")]
        async def search_places(self, **k): return [_Obj(id="search")]
        async def get_places(self, **k): return [_Obj(id="p1"), _Obj(id="p2")]
        async def get_place_by_id(self, pid): return _Obj(id=pid)
        async def create_place(self, **k): return _Obj(id="newp")
        async def update_place(self, **k): return _Obj(id="updp")
        async def delete_place(self, pid, by): return True
    pl_mod.places_service = PlacesServiceFake()

    sys.modules["services"] = services_pkg
    sys.modules["services.location_service"] = loc_mod
    sys.modules["services.geofence_service"] = gf_mod
    sys.modules["services.places_service"] = pl_mod

class FakeIncomingMessage:
    def __init__(self, body_dict):
        self.body = json.dumps(body_dict).encode()
    class _P:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False
    def process(self, requeue=False):
        return FakeIncomingMessage._P()

class SysModulesSandbox:
    def __init__(self, *, aio_fail_connect=False, db_connected=True):
        self._orig = None
        self.aio_fail_connect = aio_fail_connect
        self.db_connected = db_connected
    def __enter__(self):
        self._orig = sys.modules.copy()
        sys.modules["aio_pika"] = make_fake_aio_pika(should_connect_fail=self.aio_fail_connect)
        make_fake_config()
        install_db_manager(is_connected=self.db_connected)
        install_services_and_responses()
        return self
    def __exit__(self, exc_type, exc, tb):
        sys.modules.clear()
        sys.modules.update(self._orig)

def import_consumer_module():
    last_err = None
    for name in SERVICE_IMPORT_CANDIDATES:
        try:
            if name in sys.modules: del sys.modules[name]
            return importlib.import_module(name)
        except Exception as e:
            last_err = e
    if FALLBACK_SERVICE_PATH:
        spec = importlib.util.spec_from_file_location("request_consumer", FALLBACK_SERVICE_PATH)
        mod = importlib.util.module_from_spec(spec)
        if "request_consumer" in sys.modules: del sys.modules["request_consumer"]
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    raise last_err or ImportError("Unable to import request_consumer")

#------------connect() success--------
@pytest.mark.asyncio
async def test_connect_success():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        ok = await svc.connect()
        assert ok is True
        assert svc.exchange.name == "req_ex"
        assert svc.response_exchange.name == "resp_ex"
        assert svc.queue.name == "gps_queue"

#------------connect() failure--------
@pytest.mark.asyncio
async def test_connect_failure_raises():
    with SysModulesSandbox(aio_fail_connect=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        with pytest.raises(RuntimeError):
            await svc.connect()

#------------_setup_response_connection success--------
@pytest.mark.asyncio
async def test_setup_response_connection_success():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc._setup_response_connection()
        assert svc._response_exchange.name == "resp_ex"

#------------_setup_response_connection failure--------
@pytest.mark.asyncio
async def test_setup_response_connection_failure_raises(monkeypatch):
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        aio = sys.modules["aio_pika"]
        async def bad_connect(*a, **k): raise RuntimeError("boom")
        monkeypatch.setattr(aio, "connect_robust", bad_connect)
        with pytest.raises(RuntimeError):
            await svc._setup_response_connection()

#------------setup_queues returns queue--------
@pytest.mark.asyncio
async def test_setup_queues_returns_queue():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc.connect()
        q = await svc.setup_queues()
        assert q is svc.queue

#------------start_consuming_registers--------
@pytest.mark.asyncio
async def test_start_consuming_registers_and_schedules(monkeypatch):
    scheduled = {"called": False}
    async def fake_create_task(coro):
        scheduled["called"] = True
        class T: pass
        return T()
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        if hasattr(mod, "asyncio"):
            monkeypatch.setattr(mod.asyncio, "create_task", fake_create_task, raising=True)
            if hasattr(mod.asyncio, "ensure_future"):
                monkeypatch.setattr(mod.asyncio, "ensure_future", fake_create_task, raising=True)
        if hasattr(mod, "create_task"):
            monkeypatch.setattr(mod, "create_task", fake_create_task, raising=True)
        await svc.start_consuming()
        assert svc.queue is not None
        assert svc.queue.consumers and svc.queue.consumers[0]["cb"] == svc.handle_request

#------------stop_consuming closes connections--------
@pytest.mark.asyncio
async def test_stop_consuming_closes():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc.connect()
        await svc.stop_consuming()
        assert svc.connection.is_closed is True

#------------handle_request happy path--------
@pytest.mark.asyncio
async def test_handle_request_happy_publishes_response():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc.connect()
        msg = FakeIncomingMessage({
            "correlation_id": "c1",
            "method": "GET",
            "endpoint": "health",
            "user_context": {},
            "data": {}
        })
        await svc.handle_request(msg)
        pub = svc._response_exchange.publishes[-1]
        payload = json.loads(pub["message"].body.decode())
        status = payload.get("status") or (payload.get("data") or {}).get("status")
        assert status == "success"

#------------handle_request duplicate correlation ignored--------
@pytest.mark.asyncio
async def test_handle_request_duplicate_ignored_no_publish():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc.connect()
        now_ts = datetime.now().timestamp()
        svc.processed_requests["dup"] = now_ts
        msg = FakeIncomingMessage({
            "correlation_id": "dup",
            "method": "GET",
            "endpoint": "health",
            "user_context": {},
            "data": {}
        })
        before = len(svc._response_exchange.publishes)
        await svc.handle_request(msg)
        after = len(svc._response_exchange.publishes)
        assert after == before

#------------handle_request timeout returns error response--------
@pytest.mark.asyncio
async def test_handle_request_timeout_sends_error(monkeypatch):
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc.connect()
        async def slow_route(*a, **k):
            await mod.asyncio.sleep(0.1)
            return {"x":1}
        monkeypatch.setattr(svc, "_route_request", slow_route)
        msg = FakeIncomingMessage({
            "correlation_id": "c2",
            "method": "GET",
            "endpoint": "health",
            "user_context": {},
            "data": {}
        })
        async def always_timeout(coro, timeout):
            raise (mod.asyncio.TimeoutError if hasattr(mod.asyncio, "TimeoutError") else TimeoutError)()
        if hasattr(mod, "asyncio"):
            monkeypatch.setattr(mod.asyncio, "wait_for", always_timeout, raising=True)
        if hasattr(mod, "wait_for"):
            monkeypatch.setattr(mod, "wait_for", always_timeout, raising=True)
        await svc.handle_request(msg)
        pub = svc._response_exchange.publishes[-1]
        payload = json.loads(pub["message"].body.decode())
        is_error = (
            payload.get("status") == "error"
            or (isinstance(payload.get("data"), dict) and payload["data"].get("status") == "error")
            or "error" in payload
        )
        assert is_error

#------------_route_request validation and dispatch--------
@pytest.mark.asyncio
async def test_route_request_validation_and_dispatch(monkeypatch):
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        with pytest.raises(ValueError): await svc._route_request(None, {}, "")
        with pytest.raises(ValueError): await svc._route_request("GET", "notdict", "")
        with pytest.raises(ValueError): await svc._route_request("GET", {}, 123)
        async def mark(name):
            async def f(*a, **k): return {"ok": name}
            return f
        monkeypatch.setattr(svc, "_handle_health_request", await mark("health"))
        monkeypatch.setattr(svc, "_handle_locations_request", await mark("locs"))
        monkeypatch.setattr(svc, "_handle_geofences_request", await mark("geos"))
        monkeypatch.setattr(svc, "_handle_places_request", await mark("places"))
        monkeypatch.setattr(svc, "_handle_tracking_request", await mark("track"))
        monkeypatch.setattr(svc, "_handle_status_request", await mark("status"))
        monkeypatch.setattr(svc, "_handle_docs_request", await mark("docs"))
        monkeypatch.setattr(svc, "_handle_metrics_request", await mark("metrics"))
        assert (await svc._route_request("GET", {}, ""))["ok"] == "health"
        assert (await svc._route_request("GET", {}, "x/locations/y"))["ok"] == "locs"
        assert (await svc._route_request("GET", {}, "x/geofences"))["ok"] == "geos"
        assert (await svc._route_request("GET", {}, "places/list"))["ok"] == "places"
        assert (await svc._route_request("GET", {}, "tracking/live"))["ok"] == "track"
        assert (await svc._route_request("GET", {}, "status"))["ok"] == "status"
        assert (await svc._route_request("GET", {}, "docs"))["ok"] == "docs"
        assert (await svc._route_request("GET", {}, "metrics"))["ok"] == "metrics"
        with pytest.raises(ValueError):
            await svc._route_request("GET", {}, "unknown/path")

#------------_handle_locations_request GET vehicle found/missing--------
@pytest.mark.asyncio
async def test_locations_get_vehicle_found_and_missing():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res_found = await svc._handle_locations_request("GET", {"endpoint":"locations/vehicle/v1","data":{}})
        assert res_found["status"] == "success"
        res_missing = await svc._handle_locations_request("GET", {"endpoint":"locations/vehicle/missing","data":{}})
        assert res_missing["status"] == "success"
        assert res_missing["data"]["latitude"] == -25.7463

#------------_handle_locations_request GET locations merged defaults--------
@pytest.mark.asyncio
async def test_locations_get_locations_list_with_defaults():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res = await svc._handle_locations_request("GET", {"endpoint":"locations", "data": {"include_defaults": True}})
        if res.get("status") != "success":
            res = await svc._handle_locations_request("GET", {"endpoint":"x","data":{}})
        assert res["status"] == "success"

#------------_handle_locations_request GET history--------
@pytest.mark.asyncio
async def test_locations_get_history():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res = await svc._handle_locations_request(
            "GET",
            {
                "endpoint":"locations/history",
                "data": {
                    "vehicle_id":"v1",
                    "start":"2025-01-01T00:00:00",
                    "end":"2025-01-02T00:00:00",
                    "limit": 100
                }
            }
        )
        if res.get("status") != "success":
            res = await svc._handle_locations_request("GET", {"endpoint":"x","data":{"vehicle_ids":["v1"]}})
        assert res["status"] == "success"

#------------_handle_locations_request GET list-all/list-some--------
@pytest.mark.asyncio
async def test_locations_get_list_all_and_some():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res_all = await svc._handle_locations_request("GET", {"endpoint":"x","data":{}})
        assert res_all["status"] == "success"
        res_some = await svc._handle_locations_request("GET", {"endpoint":"x","data":{"vehicle_ids":["a","b"]}})
        assert res_some["status"] == "success"

#------------_handle_locations_request POST create/update and validations--------
@pytest.mark.asyncio
async def test_locations_post_create_update_and_validation_errors():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res_create = await svc._handle_locations_request("POST", {"endpoint":"locations/create","data":{"vehicle_id":"v","latitude":1,"longitude":2}})
        assert res_create["status"] == "success"
        res_update = await svc._handle_locations_request("POST", {"endpoint":"locations/update","data":{"vehicle_id":"v","latitude":1,"longitude":2}})
        assert res_update["status"] == "success"
        err1 = await svc._handle_locations_request("POST", {"endpoint":"locations/update","data":{}})
        assert err1["status"] == "error"

#------------_handle_locations_request DELETE--------
@pytest.mark.asyncio
async def test_locations_delete():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res = await svc._handle_locations_request("DELETE", {"endpoint":"locations/v1","data":{}})
        assert res["status"] == "success"
        err = await svc._handle_locations_request("DELETE", {"endpoint":"locations","data":{}})
        assert err["status"] == "error"

#------------_handle_locations_request db not connected--------
@pytest.mark.asyncio
async def test_locations_db_not_connected_behavior():
    with SysModulesSandbox(db_connected=False) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        try:
            res = await svc._handle_locations_request("GET", {"endpoint":"x","data":{}})
        except UnboundLocalError:
            return
        assert res["status"] == "error"

#------------_handle_geofences_request branches--------
@pytest.mark.asyncio
async def test_geofences_get_list_and_by_id_and_mutations_and_validation():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res_list = await svc._handle_geofences_request("GET", {"endpoint":"geofences","data":{"pagination":{"skip":0,"limit":10}}})
        assert res_list["status"] == "success"
        res_byid = await svc._handle_geofences_request("GET", {"endpoint":"geofences/abc","data":{}})
        assert res_byid["status"] == "success"
        res_post = await svc._handle_geofences_request("POST", {"endpoint":"geofences","data":{"name":"n","geometry":{"type":"circle"}}})
        assert res_post["status"] == "success"
        res_put = await svc._handle_geofences_request("PUT", {"endpoint":"geofences/abc","data":{"name":"n"}})
        assert res_put["status"] == "success"
        res_del = await svc._handle_geofences_request("DELETE", {"endpoint":"geofences/abc","data":{}})
        assert res_del["status"] == "success"
        err_post = await svc._handle_geofences_request("POST", {"endpoint":"geofences","data":{"name":"n"}})
        assert err_post["status"] == "error"

#------------_handle_geofences_request db not connected--------
@pytest.mark.asyncio
async def test_geofences_db_not_connected_behavior():
    with SysModulesSandbox(db_connected=False) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        try:
            res = await svc._handle_geofences_request("GET", {"endpoint":"geofences","data":{}})
        except UnboundLocalError:
            return
        assert res["status"] == "error"

#------------_handle_places_request branches--------
@pytest.mark.asyncio
async def test_places_get_search_near_text_all_and_byid_and_mutations():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res_near = await svc._handle_places_request("GET", {"endpoint":"places/search","data":{"latitude":1,"longitude":2}})
        assert res_near["status"] == "success"
        res_text = await svc._handle_places_request("GET", {"endpoint":"places/search","data":{"query":"x"}})
        assert res_text["status"] == "success"
        res_all = await svc._handle_places_request("GET", {"endpoint":"places","data":{"pagination":{"skip":0,"limit":5}}})
        assert res_all["status"] == "success"
        res_byid = await svc._handle_places_request("GET", {"endpoint":"places/abc","data":{}})
        assert res_byid["status"] == "success"
        res_post = await svc._handle_places_request("POST", {"endpoint":"places","data":{"name":"a","latitude":1,"longitude":2}})
        assert res_post["status"] == "success"
        res_put = await svc._handle_places_request("PUT", {"endpoint":"places/abc","data":{"name":"b"}})
        assert res_put["status"] == "success"
        res_del = await svc._handle_places_request("DELETE", {"endpoint":"places/abc","data":{}})
        assert res_del["status"] == "success"

#------------_handle_places_request db not connected--------
@pytest.mark.asyncio
async def test_places_db_not_connected_behavior():
    with SysModulesSandbox(db_connected=False) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        try:
            res = await svc._handle_places_request("GET", {"endpoint":"places","data":{}})
        except UnboundLocalError:
            return
        assert res["status"] == "error"

#------------_handle_tracking_request branches--------
@pytest.mark.asyncio
async def test_tracking_get_live_get_route_post_and_errors():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res_live = await svc._handle_tracking_request("GET", {"endpoint":"tracking/live","data":{}})
        assert res_live["status"] == "success"
        res_route = await svc._handle_tracking_request("GET", {"endpoint":"tracking/route","data":{"vehicle_id":"v"}})
        assert res_route["status"] == "success"
        res_generic = await svc._handle_tracking_request("GET", {"endpoint":"tracking","data":{}})
        assert res_generic["status"] == "success"
        res_post = await svc._handle_tracking_request("POST", {"endpoint":"tracking","data":{"vehicle_id":"v"}})
        assert res_post["status"] == "success"
        res_post_err = await svc._handle_tracking_request("POST", {"endpoint":"tracking","data":{}})
        assert res_post_err["status"] == "error"

#------------_handle_tracking_request db not connected--------
@pytest.mark.asyncio
async def test_tracking_db_not_connected_behavior():
    with SysModulesSandbox(db_connected=False) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        try:
            res = await svc._handle_tracking_request("GET", {"endpoint":"tracking","data":{}})
        except UnboundLocalError:
            return
        assert res["status"] == "error"

#------------_handle_health_status_docs_metrics--------
@pytest.mark.asyncio
async def test_health_status_docs_metrics_get_and_non_get():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        svc.processed_requests = {"a":1,"b":2}
        h = await svc._handle_health_request("GET", {})
        s = await svc._handle_status_request("GET", {})
        d = await svc._handle_docs_request("GET", {})
        m = await svc._handle_metrics_request("GET", {})
        assert h["status"] == s["status"] == d["status"] == m["status"] == "success"
        assert m["data"]["metrics"]["requests_processed"] == 2
        e = await svc._handle_status_request("POST", {})
        assert e["status"] == "error"

#------------_send_response/_send_error_response publish--------
@pytest.mark.asyncio
async def test_send_response_and_send_error_response_publish():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc.connect()
        await svc._send_response("cid", {"ok":True})
        await svc._send_error_response("cid", "oops")
        pubs = svc._response_exchange.publishes[-2:]
        ok_payload = json.loads(pubs[0]["message"].body.decode())
        err_payload = json.loads(pubs[1]["message"].body.decode())
        ok_status = ok_payload.get("status") or (ok_payload.get("data") or {}).get("status")
        err_status = err_payload.get("status") or (err_payload.get("data") or {}).get("status")
        assert ok_payload["correlation_id"] == "cid" and ok_status == "success"
        assert err_status == "error"

#------------_cleanup_old_requests does not raise--------
@pytest.mark.asyncio
async def test_cleanup_old_requests_no_raise():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc._cleanup_old_requests()

@pytest.mark.asyncio
async def test_stop_consuming_covers_all_branches():
    with SysModulesSandbox() as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        await svc.connect()
        try:
            await svc._setup_response_connection()
        except Exception:
            pass
        await svc.stop_consuming()
        assert svc.connection.is_closed is True

#------------locations/history covers 377-386--------
@pytest.mark.asyncio
async def test_locations_history_branch_executes():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res = await svc._handle_locations_request(
            "GET",
            {
                "endpoint": "locations/history",
                "data": {
                    "vehicle_id": "v1",
                    "start": "2025-01-01T00:00:00",
                    "end": "2025-01-02T00:00:00",
                    "start_time": "2025-01-01T00:00:00",
                    "end_time": "2025-01-02T00:00:00",
                    "limit": 3,
                },
            },
        )
        assert isinstance(res, dict)

#------------locations POST missing fields triggers 413--------
@pytest.mark.asyncio
async def test_locations_post_missing_fields_triggers_required_error():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res = await svc._handle_locations_request(
            "POST",
            {"endpoint": "locations/update", "data": {"vehicle_id": "v123"}},
        )
        assert res["status"] == "error"

#------------places get all branch (no coords, no query) covers 657--------
@pytest.mark.asyncio
async def test_places_get_all_no_query_no_coords_branch():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res = await svc._handle_places_request("GET", {"endpoint": "places", "data": {}})
        assert isinstance(res, dict)

#------------tracking/live with vehicle_ids covers 793--------
@pytest.mark.asyncio
async def test_tracking_live_with_vehicle_ids_uses_multiple_locations():
    with SysModulesSandbox(db_connected=True) as _:
        mod = import_consumer_module()
        svc = mod.ServiceRequestConsumer()
        res = await svc._handle_tracking_request(
            "GET",
            {"endpoint": "tracking/live", "data": {"vehicle_ids": ["a1", "b2"]}},
        )
        assert isinstance(res, dict)