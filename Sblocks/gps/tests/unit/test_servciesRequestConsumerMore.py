import sys
import types
import json
import importlib.util
import os
import asyncio
import time
import pytest

#------------helpers--------
def build_fake_aio_pika():
    aio = types.ModuleType("aio_pika")
    class DeliveryMode:
        PERSISTENT = 2
    aio.DeliveryMode = DeliveryMode
    class Message:
        def __init__(self, body, delivery_mode=None, content_type=None, headers=None):
            self.body = body
            self.delivery_mode = delivery_mode
            self.content_type = content_type
            self.headers = headers or {}
    aio.Message = Message
    class ExchangeType:
        DIRECT = "direct"
    aio.ExchangeType = ExchangeType
    class FakeConnection:
        def __init__(self):
            self.is_closed = False
        async def channel(self):
            return FakeChannel()
        async def close(self):
            self.is_closed = True
    class FakeExchange:
        def __init__(self, name):
            self.name = name
            self.published = []
        async def publish(self, message, routing_key=""):
            self.published.append((routing_key, message))
    class FakeQueue:
        def __init__(self, name):
            self.name = name
            self.binds = []
            self.consumer = None
        async def bind(self, exchange, routing_key=""):
            self.binds.append((exchange.name, routing_key))
        async def consume(self, callback, no_ack=False):
            self.consumer = callback
    class FakeChannel:
        def __init__(self):
            self.q = None
        async def declare_exchange(self, name, xtype, durable=True):
            return FakeExchange(name)
        async def declare_queue(self, name, durable=True):
            self.q = FakeQueue(name)
            return self.q
    async def connect_robust(url=None, heartbeat=None, blocked_connection_timeout=None):
        return FakeConnection()
    aio.connect_robust = connect_robust
    abc = types.ModuleType("aio_pika.abc")
    class AbstractIncomingMessage: ...
    abc.AbstractIncomingMessage = AbstractIncomingMessage
    sys.modules["aio_pika"] = aio
    sys.modules["aio_pika.abc"] = abc
    return aio

def install_fake_dependencies():
    build_fake_aio_pika()

    cfg_mod = types.ModuleType("config.rabbitmq_config")
    class RabbitMQConfig:
        CONNECTION_PARAMS = {"heartbeat": 10, "blocked_connection_timeout": 5}
        EXCHANGE_NAMES = {"requests": "req", "responses": "resp"}
        QUEUE_NAMES = {"gps": "gps_q"}
        ROUTING_KEYS = {"gps": "gps.route", "core_responses": "core.responses"}
        def get_rabbitmq_url(self):
            return "amqp://guest:guest@localhost/"
    def json_serializer(o):
        try:
            return o.__dict__
        except Exception:
            return str(o)
    cfg_mod.RabbitMQConfig = RabbitMQConfig
    cfg_mod.json_serializer = json_serializer
    sys.modules["config.rabbitmq_config"] = cfg_mod

    repo = types.ModuleType("repositories.database")
    class _DB:
        def __init__(self):
            self._connected = True
        def is_connected(self): return self._connected
        def set_connected(self, val): self._connected = val
    db_manager = _DB()
    repo.db_manager = db_manager
    sys.modules["repositories.database"] = repo

    sch = types.ModuleType("schemas.responses")
    class ResponseBuilder:
        @staticmethod
        def success(data=None, message=""):
            return types.SimpleNamespace(model_dump=lambda: {"status":"success","data":data,"message":message})
        @staticmethod
        def error(error="", message=""):
            return types.SimpleNamespace(model_dump=lambda: {"status":"error","error":error or {"type":"Error","message":message},"message":message})
    sch.ResponseBuilder = ResponseBuilder
    sys.modules["schemas.responses"] = sch

    loc = types.ModuleType("services.location_service")
    class _Obj:
        def __init__(self, **d):
            for k, v in d.items():
                setattr(self, k, v)
        def model_dump(self):
            return dict(self.__dict__)
    class LocationService:
        async def get_vehicle_location(self, vehicle_id):
            if vehicle_id == "missing": return None
            return _Obj(vehicle_id=vehicle_id, latitude=1.0, longitude=2.0, id="loc-"+vehicle_id)
        async def get_all_vehicle_locations(self):
            return [_Obj(vehicle_id="v1", latitude=1.1, longitude=2.2, id="loc-v1")]
        async def get_all_vehicles(self):
            return [{"_id":"v1"},{"_id":"v2"}]
        async def get_location_history(self, vehicle_id, start, end, limit):
            return [_Obj(vehicle_id=vehicle_id, latitude=9.9, longitude=8.8, id="h1")]
        async def update_vehicle_location(self, **kw):
            return {"updated": True, "payload": kw}
        async def get_vehicle_route(self, vehicle_id, start, end):
            return [{"lat":1,"lon":2},{"lat":3,"lon":4}]
        async def start_tracking(self, vehicle_id):
            return {"tracking": True, "vehicle_id": vehicle_id}
    loc.location_service = LocationService()
    sys.modules["services.location_service"] = loc

    gf = types.ModuleType("services.geofence_service")
    class _GFObj:
        def __init__(self, **d):
            for k, v in d.items():
                setattr(self, k, v)
        def model_dump(self): return dict(self.__dict__)
    class GeofenceService:
        async def get_geofence_by_id(self, gid):
            if gid == "none": return None
            return _GFObj(id=gid, name="G", geometry={"type":"circle"})
        async def get_geofences(self, **kw):
            return [_GFObj(id="g1"), _GFObj(id="g2")]
        async def create_geofence(self, **kw):
            return _GFObj(id="new", **kw)
        async def update_geofence(self, **kw):
            return _GFObj(id=kw.get("geofence_id","u"), **kw)
        async def delete_geofence(self, gid):
            return True
    gf.geofence_service = GeofenceService()
    sys.modules["services.geofence_service"] = gf

    pl = types.ModuleType("services.places_service")
    class _PObj:
        def __init__(self, **d):
            for k, v in d.items():
                setattr(self, k, v)
        def model_dump(self): return dict(self.__dict__)
    class PlacesService:
        async def get_place_by_id(self, pid):
            if pid == "none": return None
            return _PObj(id=pid, name="P")
        async def get_places(self, **kw):
            return [_PObj(id="p1"), _PObj(id="p2")]
        async def get_places_near_location(self, **kw):
            return [_PObj(id="np1"), _PObj(id="np2")]
        async def search_places(self, **kw):
            return [_PObj(id="s1")]
        async def create_place(self, **kw):
            return _PObj(id="new", **kw)
        async def update_place(self, **kw):
            return _PObj(id=kw.get("place_id","u"), **kw)
        async def delete_place(self, pid, deleted_by):
            return True
    pl.places_service = PlacesService()
    sys.modules["services.places_service"] = pl

def import_consumer_module():
    install_fake_dependencies()
    candidates = [
        os.path.join("services","request_consumer.py"),
        os.path.join("gps","services","request_consumer.py"),
        os.path.join(os.getcwd(), "services","request_consumer.py"),
        os.path.join(os.getcwd(), "gps","services","request_consumer.py"),
        os.path.join(os.getcwd(), "request_consumer.py"),
        "/mnt/data/request_consumer.py",
    ]
    path = next((p for p in candidates if p and os.path.exists(p)), None)
    assert path, "request_consumer.py not found"
    spec = importlib.util.spec_from_file_location("services.request_consumer", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["services.request_consumer"] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod

#------------start_consuming error path--------
@pytest.mark.asyncio
async def test_start_consuming_error_path():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    await svc.connect()
    async def boom(*a, **k): raise RuntimeError("consume fail")
    svc.queue.consume = boom
    with pytest.raises(RuntimeError):
        await svc.start_consuming()

#------------stop_consuming closes both--------
@pytest.mark.asyncio
async def test_stop_consuming_closes_both():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    await svc.connect()
    await svc._setup_response_connection()
    await svc.stop_consuming()
    assert svc.connection.is_closed is True

#------------disconnect closes both--------
@pytest.mark.asyncio
async def test_disconnect_closes_both():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    await svc.connect()
    await svc._setup_response_connection()
    await svc.disconnect()
    assert svc.connection.is_closed is True

#------------locations list defaults--------
@pytest.mark.asyncio
async def test_locations_get_locations_list_with_defaults_success():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_locations_request("GET", {"endpoint": "locations", "data":{"include_defaults": True}})
    assert res["status"] == "success"
    data = res["data"]
    assert isinstance(data, list)
    ids = [item.get("id") if isinstance(item, dict) else getattr(item, "id", "") for item in data]
    assert any(isinstance(i, str) and (i.startswith("loc-") or i.startswith("default_")) for i in ids)

#------------locations history--------
@pytest.mark.asyncio
async def test_locations_get_history_success():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_locations_request("GET", {"endpoint": "locations/history", "data":{"vehicle_id":"v1","start_time":"2020-01-01T00:00:00","end_time":"2020-01-02T00:00:00","limit":5}})
    assert res["status"] == "success"
    data = res["data"]
    assert data is not None

#------------locations post validation--------
@pytest.mark.asyncio
async def test_locations_post_requires_vehicle_lat_lon_error():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_locations_request("POST", {"endpoint": "locations/update", "data": {}})
    assert res["status"] == "error"

#------------geofences user_context str--------
@pytest.mark.asyncio
async def test_geofences_user_context_is_string_and_not_found_branch():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    user_context = json.dumps({"endpoint":"geofences/none","data":{}})
    res = await svc._handle_geofences_request("GET", user_context)
    assert res["status"] == "success"
    assert res["data"] is None

#------------geofences post missing data--------
@pytest.mark.asyncio
async def test_geofences_post_missing_data_error():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_geofences_request("POST", {"endpoint":"geofences","data":{}})
    assert res["status"] == "error"

#------------geofences create failure--------
@pytest.mark.asyncio
async def test_geofences_post_create_failure_error(monkeypatch):
    mod = import_consumer_module()
    async def create_none(**kw): return None
    sys.modules["services.geofence_service"].geofence_service.create_geofence = create_none
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_geofences_request("POST", {"endpoint":"geofences","data":{"name":"n","geometry":{"type":"circle","center":{"latitude":1,"longitude":2},"radius":5}}})
    assert res["status"] == "error"

#------------geofences put missing id and data--------
@pytest.mark.asyncio
async def test_geofences_put_missing_id_and_data_errors():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    res1 = await svc._handle_geofences_request("PUT", {"endpoint":"geofences","data":{"name":"x"}})
    assert res1["status"] == "error"
    res2 = await svc._handle_geofences_request("PUT", {"endpoint":"geofences/abc","data":{}})
    assert res2["status"] == "error"

#------------geofences update failure--------
@pytest.mark.asyncio
async def test_geofences_put_update_failure_error(monkeypatch):
    mod = import_consumer_module()
    async def upd_none(**kw): return None
    sys.modules["services.geofence_service"].geofence_service.update_geofence = upd_none
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_geofences_request("PUT", {"endpoint":"geofences/abc","data":{"name":"x","geometry":{"type":"polygon","points":[{"latitude":1,"longitude":2},{"latitude":2,"longitude":3},{"latitude":3,"longitude":4}]}}})
    assert res["status"] == "error"

#------------geofences delete missing id--------
@pytest.mark.asyncio
async def test_geofences_delete_missing_id_and_unsupported_method():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_geofences_request("DELETE", {"endpoint":"geofences","data":{}})
    assert res["status"] == "error"
    res2 = await svc._handle_geofences_request("PATCH", {"endpoint":"geofences","data":{}})
    assert res2["status"] == "error"

#------------places get all and errors--------
@pytest.mark.asyncio
async def test_places_get_all_and_missing_data_errors(monkeypatch):
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_places_request("GET", {"endpoint":"places","data":{"pagination":{"skip":0,"limit":5}}})
    assert res["status"] == "success"
    res2 = await svc._handle_places_request("POST", {"endpoint":"places","data":{}})
    assert res2["status"] == "error"

#------------places put delete and unsupported--------
@pytest.mark.asyncio
async def test_places_put_delete_and_unsupported_errors():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    r1 = await svc._handle_places_request("PUT", {"endpoint":"places","data":{"name":"x"}})
    assert r1["status"] == "error"
    r2 = await svc._handle_places_request("PUT", {"endpoint":"places/abc","data":{}})
    assert r2["status"] == "error"
    r3 = await svc._handle_places_request("DELETE", {"endpoint":"places","data":{}})
    assert r3["status"] == "error"
    r4 = await svc._handle_places_request("PATCH", {"endpoint":"places","data":{}})
    assert r4["status"] == "error"

#------------places exception path--------
@pytest.mark.asyncio
async def test_places_exception_path_returns_error(monkeypatch):
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    async def boom(**kw): raise RuntimeError("db fail")
    sys.modules["services.places_service"].places_service.get_places = boom
    res = await svc._handle_places_request("GET", {"endpoint":"places","data":{}})
    assert res["status"] == "error"

#------------tracking route missing id and unsupported--------
@pytest.mark.asyncio
async def test_tracking_route_missing_id_and_unsupported():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    res = await svc._handle_tracking_request("GET", {"endpoint":"tracking/route","data":{}})
    assert res["status"] == "error"
    r2 = await svc._handle_tracking_request("PATCH", {"endpoint":"tracking","data":{}})
    assert r2["status"] == "error"

#------------tracking post missing data and vehicle id--------
@pytest.mark.asyncio
async def test_tracking_post_missing_data_and_vehicle_id():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    r1 = await svc._handle_tracking_request("POST", {"endpoint":"tracking","data":{}})
    assert r1["status"] == "error"
    r2 = await svc._handle_tracking_request("POST", {"endpoint":"tracking","data":{"foo":"bar"}})
    assert r2["status"] == "error"

#------------health/docs/metrics unsupported--------
@pytest.mark.asyncio
async def test_health_docs_metrics_unsupported_methods():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    h = await svc._handle_health_request("POST", {})
    d = await svc._handle_docs_request("POST", {})
    m = await svc._handle_metrics_request("POST", {})
    assert h["status"] == d["status"] == m["status"] == "error"

#------------send_response exception--------
@pytest.mark.asyncio
async def test_send_response_publish_exception():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    await svc._setup_response_connection()
    async def raise_pub(msg, routing_key=""):
        raise RuntimeError("publish fail")
    svc._response_exchange.publish = raise_pub
    with pytest.raises(RuntimeError):
        await svc._send_response("c1", {"status":"ok"})

#------------send_error_response exception is swallowed--------
@pytest.mark.asyncio
async def test_send_error_response_publish_exception_swallowed():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    await svc._setup_response_connection()
    async def raise_pub(msg, routing_key=""): raise RuntimeError("fail")
    svc._response_exchange.publish = raise_pub
    await svc._send_error_response("c2", "oops")

#------------cleanup_old_requests removes and logs--------
@pytest.mark.asyncio
async def test_cleanup_old_requests_cleans():
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    now = time.time()
    svc._request_hashes = {"h1": now - 7200, "h2": now}
    svc._pending_requests = {"r1": now - 7200, "r2": now}
    await svc._cleanup_old_requests()
    assert "h1" not in svc._request_hashes and "r1" not in svc._pending_requests

#------------start_cleanup_task runs loop paths--------
@pytest.mark.asyncio
async def test_start_cleanup_task_error_then_exit(monkeypatch):
    mod = import_consumer_module()
    svc = mod.ServiceRequestConsumer()
    calls = {"n":0}
    async def fake_sleep(delay):
        calls["n"] += 1
        if calls["n"] == 1:
            return
        else:
            raise SystemExit
    monkeypatch.setattr(mod, "asyncio", types.SimpleNamespace(sleep=fake_sleep, create_task=asyncio.create_task, wait_for=asyncio.wait_for))
    async def boom():
        raise Exception("boom")
    svc._cleanup_old_requests = boom
    with pytest.raises(SystemExit):
        await svc._start_cleanup_task()

