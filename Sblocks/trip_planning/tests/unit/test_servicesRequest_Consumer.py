# tests/unit/test_servicesRequest_Consumer.py
import sys, os, types, importlib.util, json, pytest
from datetime import datetime, timedelta, timezone

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..", "services", "request_consumer.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "management", "services", "request_consumer.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "request_consumer.py")),
    os.path.abspath(os.path.join(os.getcwd(), "services", "request_consumer.py")),
    os.path.abspath(os.path.join(os.getcwd(), "request_consumer.py")),
]

def _snapshot(names):
    return {n: sys.modules.get(n) for n in names}

def _restore(snap):
    for name, orig in snap.items():
        if orig is None:
            if name in sys.modules:
                del sys.modules[name]
        else:
            sys.modules[name] = orig

def _ensure(name, as_pkg=False):
    if name not in sys.modules:
        m = types.ModuleType(name)
        if as_pkg:
            m.__path__ = []
        sys.modules[name] = m
    return sys.modules[name]

def _install_stubs():
    # -------- aio_pika stub --------
    aio_pika = _ensure("aio_pika")
    aio_pika_abc = _ensure("aio_pika.abc")
    class AbstractIncomingMessage: ...
    aio_pika_abc.AbstractIncomingMessage = AbstractIncomingMessage

    class ExchangeType:
        DIRECT = "direct"
    aio_pika.ExchangeType = ExchangeType

    class DeliveryMode:
        PERSISTENT = 2
    aio_pika.DeliveryMode = DeliveryMode

    class Message:
        def __init__(self, body, delivery_mode=None, content_type=None, headers=None):
            self.body = body
            self.delivery_mode = delivery_mode
            self.content_type = content_type
            self.headers = headers or {}
    aio_pika.Message = Message

    class _Exchange:
        def __init__(self, name):
            self.name = name
            self.published = []
        async def publish(self, message, routing_key=""):
            self.published.append((message, routing_key))

    class _Queue:
        def __init__(self, name):
            self.name = name
            self.bound = []
            self.handler = None
        async def bind(self, exchange, routing_key):
            self.bound.append((exchange.name if hasattr(exchange, "name") else exchange, routing_key))
        async def consume(self, handler, no_ack=False):
            self.handler = handler

    class _Channel:
        def __init__(self):
            self.exchanges = {}
            self.queues = {}
        async def declare_exchange(self, name, typ, durable=True):
            ex = _Exchange(name)
            self.exchanges[name] = ex
            return ex
        async def declare_queue(self, name, durable=True):
            q = _Queue(name)
            self.queues[name] = q
            return q

    class _Connection:
        def __init__(self):
            self._channel = _Channel()
            self.is_closed = False
        async def channel(self):
            return self._channel
        async def close(self):
            self.is_closed = True

    async def connect_robust(url, heartbeat, blocked_connection_timeout):
        return _Connection()

    aio_pika.connect_robust = connect_robust
    aio_pika.AbstractIncomingMessage = object  # only for typing

    # -------- config.rabbitmq_config stub --------
    cfg_pkg = _ensure("config", as_pkg=True)
    cfg_mod = _ensure("config.rabbitmq_config")
    class RabbitMQConfig:
        QUEUE_NAMES = {"trips": "q.trips"}
        EXCHANGE_NAMES = {"requests": "ex.requests", "responses": "ex.responses"}
        ROUTING_KEYS = {"core_responses": "core.responses"}
        CONNECTION_PARAMS = {"heartbeat": 5, "blocked_connection_timeout": 10}
        REQUEST_TIMEOUTS = {"default_request_timeout": 0.5}
        def get_rabbitmq_url(self): return "amqp://guest:guest@localhost/"
    def json_serializer(obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)
    cfg_mod.RabbitMQConfig = RabbitMQConfig
    cfg_mod.json_serializer = json_serializer

    # -------- schemas.responses stub --------
    schemas_pkg = _ensure("schemas", as_pkg=True)
    resp_mod = _ensure("schemas.responses")
    class _Resp(dict):
        def model_dump(self, mode=None): return dict(self)
    class ResponseBuilder:
        @staticmethod
        def success(data=None, message=""):
            return _Resp(status="success", data=data, message=message)
        @staticmethod
        def error(error="", message=""):
            return _Resp(status="error", error=error, message=message)
    resp_mod.ResponseBuilder = ResponseBuilder

    # -------- services.* stubs used by handlers --------
    services_pkg = _ensure("services", as_pkg=True)

    # trip_service stub
    serv_trip = _ensure("services.trip_service")
    class _Model:
        def __init__(self, **d): self._d = d
        def model_dump(self): return dict(self._d)
    class _TripObj(_Model): pass
    class _TripService:
        async def list_trips(self, req): return [{"trip": "ok", "vehicle_id": getattr(req, "vehicle_id", None)}]
        async def get_vehicle_polyline(self, vid): return {"vehicle_id": vid, "polyline": "abc"}
        async def get_all_upcoming_trips(self): return [_TripObj(id="t1").model_dump()]
        async def get_upcoming_trips(self, driver_id, limit=10): return [_TripObj(id="u1").model_dump()]
        async def get_recent_trips(self, driver_id, limit=10, days=30): return [_TripObj(id="r1").model_dump()]
        async def get_all_recent_trips(self, limit, days): return [_TripObj(id="ar1").model_dump()]
        async def get_active_trips(self, driver_id=None): return [_TripObj(id="a1")]
        async def get_all_trips(self): return [_TripObj(id="x1"), _TripObj(id="x2")]
        async def create_trip(self, req, created_by): return _TripObj(id="new", driver_assignment="D1", vehicle_id="V1")
        async def start_trip(self, tid, by): return _TripObj(id=tid, started=True)
        async def pause_trip(self, tid, by): return _TripObj(id=tid, paused=True)
        async def resume_trip(self, tid, by): return _TripObj(id=tid, resumed=True)
        async def cancel_trip(self, tid, by, reason): return _TripObj(id=tid, cancelled=True)
        async def complete_trip(self, tid, by): return _TripObj(id=tid, completed=True)
        async def get_trip_by_id(self, tid): return _TripObj(id=tid, name="nm", driver_assignment="D1", vehicle_id="V1")
        async def get_trip_by_name_and_driver(self, filt): return _TripObj(id="canon", driver_assignment="D1", vehicle_id="V1")
        async def update_trip(self, trip_id, req, updated_by): return _TripObj(id=trip_id, updated=True)
        async def delete_trip(self, tid, by): return True
    serv_trip.trip_service = _TripService()

    # ancillary services used in POST branches
    serv_drv = _ensure("services.driver_service")
    class _DrvSvc:
        async def deactivateDriver(self, driver_id): return True
        async def activateDriver(self, driver_id): return True
    serv_drv.driver_service = _DrvSvc()

    serv_veh = _ensure("services.vehicle_service")
    class _VehSvc:
        async def deactiveVehicle(self, vehicle_id): return True
        async def activeVehicle(self, vehicle_id): return True
        async def removeLocation(self, vehicle_id): return True
    serv_veh.vehicle_service = _VehSvc()

    serv_va = _ensure("services.vehicle_assignments_services")
    class _VASvc:
        async def createAssignment(self, trip_id, vehicle_id, driver_id): return {"ok": True}
        async def removeAssignment(self, vehicle_id, driver_id): return True
    serv_va.vehicle_assignment_service = _VASvc()

    serv_th = _ensure("services.trip_history_service")
    class _THSvc:
        async def add_trip(self, trip): return _TripObj(id="h1", name="nm", driver_assignment="D1")
    serv_th.trip_history_service = _THSvc()

    # driver analytics
    serv_drv_an = _ensure("services.driver_analytics_service")
    class _DASvc:
        async def get_total_trips(self, timeframe): return 42
        async def get_driver_trip_stats(self, timeframe): return {"ok": 1}
        async def get_completion_rate(self, timeframe): return 0.75
        async def get_average_trips_per_day(self, timeframe): return 3.0
    serv_drv_an.driver_analytics_service = _DASvc()

    # vehicle analytics
    serv_veh_an = _ensure("services.vehicle_analytics_service")
    class _VASvc2:
        async def get_vehicle_trip_stats(self, timeframe): return {"ok": 2}
        async def get_total_distance_all_vehicles(self, timeframe): return 123.4
    serv_veh_an.vehicle_analytics_service = _VASvc2()

    # general analytics
    serv_an = _ensure("services.analytics_service")
    class _ASvc:
        def get_analytics_first(self, start, end): return {"drivers": True, "range": (start.isoformat(), end.isoformat())}
        def get_analytics_second(self, start, end): return {"vehicles": True, "range": (start.isoformat(), end.isoformat())}
        async def get_trip_history_stats(self, days=None): return {"days": days if days is not None else "default"}
    serv_an.analytics_service = _ASvc()

    # notification service
    serv_nt = _ensure("services.notification_service")
    class _Notif:
        def __init__(self, id=None, _id=None, type="t", title="T", message="M", sent_at=datetime.now(), is_read=False, trip_id=None, driver_id=None, data=None):
            self.id = id
            self._id = _id
            self.type = type; self.title = title; self.message = message
            self.sent_at = sent_at; self.is_read = is_read
            self.trip_id = trip_id; self.driver_id = driver_id; self.data = data or {}
    class _NSvc:
        async def get_user_notifications(self, user_id, unread_only=False, limit=50, skip=0):
            return ([_Notif(id="n1", is_read=False), _Notif(id="n2", is_read=True)], 2)
        async def send_notification(self, req): return [_Notif(id="X1"), _Notif(id="X2")]
        async def mark_notification_read(self, nid, uid): return nid == "ok"
    serv_nt.notification_service = _NSvc()

    # schemas.requests used in trips & notifications
    req_mod = _ensure("schemas.requests")
    class TripFilterRequest:
        def __init__(self, **d): self.__dict__.update(d)
    class CreateTripRequest:
        def __init__(self, **d): self.__dict__.update(d)
    class UpdateTripRequest:
        def __init__(self, **d): self.__dict__.update(d)
    class FinishTripRequest:
        def __init__(self, **d): self.__dict__.update(d)
    class NotificationRequest:
        def __init__(self, **d): self.__dict__.update(d)
    req_mod.TripFilterRequest = TripFilterRequest
    req_mod.CreateTripRequest = CreateTripRequest
    req_mod.UpdateTripRequest = UpdateTripRequest
    req_mod.FinishTripRequest = FinishTripRequest
    req_mod.NotificationRequest = NotificationRequest

def _load_consumer_isolated():
    names = [
        "aio_pika", "aio_pika.abc",
        "config", "config.rabbitmq_config",
        "schemas", "schemas.responses", "schemas.requests",
        "services", "services.trip_service", "services.driver_service",
        "services.vehicle_service", "services.vehicle_assignments_services",
        "services.trip_history_service", "services.driver_analytics_service",
        "services.vehicle_analytics_service", "services.analytics_service",
        "services.notification_service",
        "services.request_consumer",
    ]
    snap = _snapshot(names)
    _install_stubs()

    # import target module
    for p in CANDIDATES:
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("services.request_consumer", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.request_consumer"] = mod
            spec.loader.exec_module(mod)
            # grab class, then restore sys.modules to avoid bleeding stubs
            Service = mod.ServiceRequestConsumer
            _restore(snap)
            return mod, Service
    _restore(snap)
    raise ImportError("request_consumer.py not found")

# ---------------------- Tests ----------------------

@pytest.mark.asyncio
async def test_connect_declares_and_binds():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    # monkeypatch aio_pika in the instance namespace after restore
    # we will re-stub minimal bits used by connect() safely:
    # reuse the loader again to get stubs
    _install_stubs()
    import aio_pika
    import config.rabbitmq_config as cfg

    # run
    ok = await svc.connect()
    assert ok is True
    assert svc.queue is not None
    # queue bound to "trips.requests"
    q = svc.queue
    assert any(rk == "trips.requests" for _, rk in q.bound)
    # response exchange for publishing was created by _setup_response_connection
    assert svc._response_connection is not None

@pytest.mark.asyncio
async def test_setup_response_connection_reuse():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    _install_stubs()
    import aio_pika
    await svc._setup_response_connection()
    # second call should reuse (connection not closed) and not blow up
    prev = svc._response_connection
    await svc._setup_response_connection()
    assert svc._response_connection is prev

@pytest.mark.asyncio
async def test_stop_consuming_closes_only_main_connection():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    _install_stubs()
    import aio_pika
    # open both main and response connections
    await svc.connect()
    await svc._setup_response_connection()
    resp_conn = svc._response_connection
    # close only main via stop_consuming (the last definition takes effect)
    await svc.stop_consuming()
    assert svc.connection.is_closed is True
    # shadowed stop_consuming does NOT close the response connection
    assert resp_conn.is_closed is False

@pytest.mark.asyncio
async def test_route_request_routing_matrix(monkeypatch):
    mod, Service = _load_consumer_isolated()
    svc = Service()
    async def h_health(m,u): return {"health":"ok"}
    async def h_drv_an(m,u): return {"da":"ok"}
    async def h_veh_an(m,u): return {"va":"ok"}
    async def h_an(m,u): return {"a":"ok"}
    async def h_trips(m,u): return {"t":"ok"}
    async def h_drivers(m,u): return {"drivers":"ok"}
    async def h_notif(m,u): return {"n":"ok"}
    monkeypatch.setattr(svc, "_handle_health_request", h_health)
    monkeypatch.setattr(svc, "_handle_driver_analytics_requests", h_drv_an)
    monkeypatch.setattr(svc, "_handle_vehicle_analytics_requests", h_veh_an)
    monkeypatch.setattr(svc, "_handle_analytics_requests", h_an)
    monkeypatch.setattr(svc, "_handle_trips_request", h_trips)
    monkeypatch.setattr(svc, "_handle_drivers_request", h_drivers)
    monkeypatch.setattr(svc, "_handle_notifications_request", h_notif)

    uc = {"data":{}}
    assert await svc._route_request("GET", uc, "health") == {"health":"ok"}
    assert await svc._route_request("GET", uc, "analytics/drivers/totaltrips/week") == {"da":"ok"}
    assert await svc._route_request("GET", uc, "analytics/vehicles/stats/month") == {"va":"ok"}
    assert await svc._route_request("GET", uc, "analytics/trips/history-stats") == {"a":"ok"}
    assert await svc._route_request("GET", uc, "trips") == {"t":"ok"}
    assert await svc._route_request("GET", uc, "driver/123/recent") == {"t":"ok"}
    assert await svc._route_request("GET", uc, "drivers") == {"drivers":"ok"}
    assert await svc._route_request("GET", uc, "notifications/list") == {"n":"ok"}
    with pytest.raises(ValueError):
        await svc._route_request("GET", uc, "unknown/thing")

class _FakeMsg:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode()
        self.process_called = False
    class _Ctx:
        def __init__(self, outer): self.outer = outer
        async def __aenter__(self): self.outer.process_called = True
        async def __aexit__(self, exc_type, exc, tb): return False
    def process(self, requeue=False): return _FakeMsg._Ctx(self)

@pytest.mark.asyncio
async def test_handle_request_success_and_error(monkeypatch):
    mod, Service = _load_consumer_isolated()
    svc = Service()
    sent = []
    async def fake_send(cid, resp):
        sent.append((cid, resp))
    monkeypatch.setattr(svc, "_send_response", fake_send)
    async def good_route(method, uc, ep):
        return {"ok": True}
    async def bad_route(method, uc, ep):
        raise RuntimeError("boom")

    # success
    svc._route_request = good_route
    msg = _FakeMsg({"correlation_id":"c1","method":"GET","endpoint":"health","user_context":{},"data":{}})
    await svc.handle_request(msg)
    assert sent and sent[-1][0] == "c1" and sent[-1][1]["status"] == "success"

    # error path
    sent.clear()
    svc._route_request = bad_route
    msg2 = _FakeMsg({"correlation_id":"c2","method":"GET","endpoint":"fail","user_context":{},"data":{}})
    await svc.handle_request(msg2)
    assert sent and sent[-1][0] == "c2" and sent[-1][1]["status"] == "error"


@pytest.mark.asyncio
async def test_driver_analytics_metrics_and_unknown_and_bad_method():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    # each metric
    for metric in ("totaltrips","stats","completionrate","averagedaytrips"):
        out = await svc._handle_driver_analytics_requests("GET", {"endpoint":f"analytics/drivers/{metric}/week","data":{}})
        assert out["status"] == "success"
    # unknown metric
    out2 = await svc._handle_driver_analytics_requests("GET", {"endpoint":"analytics/drivers/unknown/week","data":{}})
    assert out2["status"] == "error"
    # bad method
    out3 = await svc._handle_driver_analytics_requests("POST", {"endpoint":"analytics/drivers/totaltrips/week","data":{}})
    assert out3["status"] == "error"

@pytest.mark.asyncio
async def test_vehicle_analytics_metrics_and_unknown():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    out1 = await svc._handle_vehicle_analytics_requests("GET", {"endpoint":"analytics/vehicles/stats/week","data":{}})
    out2 = await svc._handle_vehicle_analytics_requests("GET", {"endpoint":"analytics/vehicles/totaldistance/week","data":{}})
    out3 = await svc._handle_vehicle_analytics_requests("GET", {"endpoint":"analytics/vehicles/unknown/week","data":{}})
    assert out1["status"] == "success" and out2["status"] == "success" and out3["status"] == "error"

@pytest.mark.asyncio
async def test_analytics_requests_drivers_vehicles_and_history_stats_and_unknown():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    out1 = await svc._handle_analytics_requests("GET", {"endpoint":"analytics/drivers","data":{"timeframe":"week"}})
    assert out1["status"] == "success" and "drivers" in out1["data"]
    out2 = await svc._handle_analytics_requests("GET", {"endpoint":"analytics/vehicles","data":{"timeframe":"month"}})
    assert out2["status"] == "success" and "vehicles" in out2["data"]
    out3 = await svc._handle_analytics_requests("GET", {"endpoint":"analytics/trips/history-stats","data":{"days":"14"}})
    assert out3["status"] == "success" and out3["data"]["days"] == 14
    out4 = await svc._handle_analytics_requests("GET", {"endpoint":"analytics/unknown","data":{}})
    assert out4["status"] == "error"

@pytest.mark.asyncio
async def test_notifications_get_post_auth_and_put_mark_read():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    # GET list
    out = await svc._handle_notifications_request("GET", {"endpoint":"notifications","user_id":"u1","data":{"unread_only":"false","limit":"10","skip":"0"}})
    assert out["status"] == "success" and out["data"]["total"] == 2 and out["data"]["unread_count"] == 1
    # POST unauthorized
    out2 = await svc._handle_notifications_request("POST", {"endpoint":"notifications","user_id":"admin","role":"user","data":{}})
    assert out2["status"] == "error"
    # POST authorized
    out3 = await svc._handle_notifications_request("POST", {"endpoint":"notifications","user_id":"admin","role":"admin","data":{"user_ids":["a"],"type":"X","title":"t","message":"m"}})
    assert out3["status"] == "success" and out3["data"]["sent_count"] == 2
    # PUT mark read true
    out4 = await svc._handle_notifications_request("PUT", {"endpoint":"notifications/ok","user_id":"u1","data":{}})
    assert out4["status"] == "success" and out4["data"]["marked_read"] is True
    # PUT mark read false
    out5 = await svc._handle_notifications_request("PUT", {"endpoint":"notifications/notok","user_id":"u1","data":{}})
    assert out5["data"]["marked_read"] is False

@pytest.mark.asyncio
async def test_health_docs_metrics_get_and_bad_methods():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    assert (await svc._handle_health_request("GET", {}))["status"] == "success"
    assert (await svc._handle_health_request("POST", {}))["status"] == "error"
    assert (await svc._handle_docs_request("GET", {}))["status"] == "success"
    assert (await svc._handle_docs_request("DELETE", {}))["status"] == "error"
    assert (await svc._handle_metrics_request("GET", {}))["status"] == "success"
    assert (await svc._handle_metrics_request("PUT", {}))["status"] == "error"

@pytest.mark.asyncio
async def test_send_response_and_send_error_response_publish(monkeypatch):
    mod, Service = _load_consumer_isolated()
    svc = Service()
    # install minimal response exchange
    class _Ex:
        def __init__(self): self.pubs=[]
        async def publish(self, msg, routing_key): self.pubs.append((msg, routing_key))
    svc._response_exchange = _Ex()
    svc.config = types.SimpleNamespace(ROUTING_KEYS={"core_responses":"rk"})
    # bypass _setup_response_connection
    async def noop(): pass
    svc._setup_response_connection = noop
    await svc._send_response("c1", {"status":"success","data":{"x":1}})
    assert svc._response_exchange.pubs and svc._response_exchange.pubs[-1][1] == "rk"
    # error response
    await svc._send_error_response("c2", "bad")
    assert len(svc._response_exchange.pubs) >= 2
    body = svc._response_exchange.pubs[-1][0].body
    payload = json.loads(body.decode())
    assert payload["status"] == "error" and payload["correlation_id"] == "c2"

@pytest.mark.asyncio
async def test_cleanup_old_requests_removes_and_ignores_missing():
    mod, Service = _load_consumer_isolated()
    svc = Service()
    now = datetime.now().timestamp()
    svc._request_hashes = {"h_new": now, "h_old": now - 4000}
    svc._pending_requests = {"r_new": now, "r_old": now - 4000}
    await svc._cleanup_old_requests()
    assert "h_old" not in svc._request_hashes and "r_old" not in svc._pending_requests
    # delete attrs and ensure method doesn't raise
    del svc._request_hashes
    del svc._pending_requests
    await svc._cleanup_old_requests()
