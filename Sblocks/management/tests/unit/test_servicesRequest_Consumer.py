import sys, os, types, importlib, json, pytest
from datetime import datetime

HERE = os.path.abspath(os.path.dirname(__file__))
CANDS = [
    os.path.abspath(os.path.join(HERE, "..", "..")),
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDS:
    if p not in sys.path:
        sys.path.insert(0, p)


def _ensure_pkg(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
    if not hasattr(sys.modules[name], "__path__"):
        sys.modules[name].__path__ = []
_ensure_pkg("config"); _ensure_pkg("api"); _ensure_pkg("api.routes"); _ensure_pkg("services"); _ensure_pkg("schemas")


cfg_mod = types.ModuleType("config.rabbitmq_config")
class RabbitMQConfig:
    QUEUE_NAMES = {"management": "mgmt.queue"}
    EXCHANGE_NAMES = {"requests": "req.ex", "responses": "resp.ex"}
    ROUTING_KEYS = {"core_responses": "core.responses"}
    CONNECTION_PARAMS = {"heartbeat": 60, "blocked_connection_timeout": 30}
    def get_rabbitmq_url(self): return "amqp://guest:guest@localhost/"
def json_serializer(o):
    if isinstance(o, datetime): return o.isoformat()
    return str(o)
cfg_mod.RabbitMQConfig = RabbitMQConfig
cfg_mod.json_serializer = json_serializer
sys.modules["config.rabbitmq_config"] = cfg_mod


sys.modules["api.routes.vehicles"] = types.ModuleType("api.routes.vehicles")
sys.modules["api.routes.vehicles"].router = object()
sys.modules["api.routes.drivers"] = types.ModuleType("api.routes.drivers")
sys.modules["api.routes.drivers"].router = object()
sys.modules["api.routes.analytics"] = types.ModuleType("api.routes.analytics")
sys.modules["api.routes.analytics"].router = object()


resp_mod = types.ModuleType("schemas.responses")
class _Wrap:
    def __init__(self, d): self._d = d
    def model_dump(self): return self._d
class ResponseBuilder:
    @staticmethod
    def error(error="Error", message=""): return _Wrap({"status":"error", "error":error, "message":message})
    @staticmethod
    def success(data=None, message=""): return _Wrap({"status":"success","data":data,"message":message})
resp_mod.ResponseBuilder = ResponseBuilder
sys.modules["schemas.responses"] = resp_mod


aio_pika_pkg = types.ModuleType("aio_pika")
aio_pika_pkg.__path__ = [] 

class ExchangeType:
    DIRECT = "direct"

class FakeExchange:
    def __init__(self, name): self.name = name; self.published = []
    async def publish(self, message, routing_key): self.published.append((message, routing_key))

class FakeQueue:
    def __init__(self, name): self.name = name; self.bound = []; self.consume_args=None
    async def bind(self, exchange, routing_key): self.bound.append((exchange, routing_key))
    async def consume(self, callback, no_ack=False): self.consume_args = (callback, no_ack)

class FakeChannel:
    def __init__(self): self.exchanges = {}; self.queues = {}
    async def declare_exchange(self, name, type, durable=True):
        ex = FakeExchange(name); self.exchanges[name] = ex; return ex
    async def declare_queue(self, name, durable=True):
        q = FakeQueue(name); self.queues[name] = q; return q

class FakeConnection:
    def __init__(self): self._closed = False; self._channel = FakeChannel()
    @property
    def is_closed(self): return self._closed
    async def channel(self): return self._channel
    async def close(self): self._closed = True

async def connect_robust(url, heartbeat=None, blocked_connection_timeout=None):
    return FakeConnection()

class Message:
    def __init__(self, body: bytes, correlation_id=None):
        self.body = body
        self.correlation_id = correlation_id

aio_pika_pkg.ExchangeType = ExchangeType
aio_pika_pkg.Message = Message
aio_pika_pkg.connect_robust = connect_robust


sys.modules["aio_pika"] = aio_pika_pkg


aio_pika_abc = types.ModuleType("aio_pika.abc")

class AbstractIncomingMessage: pass


aio_pika_abc.AbstractIncomingMessage = AbstractIncomingMessage
sys.modules["aio_pika.abc"] = aio_pika_abc


FakeExchangeType = ExchangeType
FakeExchangeClass = FakeExchange
FakeQueueClass = FakeQueue
FakeChannelClass = FakeChannel
FakeConnectionClass = FakeConnection


def _load_rc_module():
    import importlib.util
    candidates = [
        os.path.abspath(os.path.join(HERE, "..", "..", "services", "request_consumer.py")),
        os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "request_consumer.py")),
        os.path.abspath(os.path.join(os.getcwd(), "services", "request_consumer.py")),
        os.path.abspath(os.path.join(os.getcwd(), "request_consumer.py")),
    ]
    for path in candidates:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("services.request_consumer", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.request_consumer"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("request_consumer.py not found")

rc_mod = _load_rc_module()
ServiceRequestConsumer = rc_mod.ServiceRequestConsumer


def make_consumer():
    return ServiceRequestConsumer()


@pytest.mark.asyncio
async def test_connect_success():
    c = make_consumer()
    ok = await c.connect()
    assert ok is True
    assert isinstance(c.exchange, FakeExchange) and c.exchange.name == c.exchange_name
    assert isinstance(c.response_exchange, FakeExchange)
    assert isinstance(c.queue, FakeQueue)
    assert c.queue.bound and c.queue.bound[-1][1] == "management.requests"

@pytest.mark.asyncio
async def test_connect_failure_raises(monkeypatch):
    c = make_consumer()
    async def boom(**kwargs): raise RuntimeError("down")
    monkeypatch.setattr(sys.modules["aio_pika"], "connect_robust", boom)
    with pytest.raises(RuntimeError):
        await c.connect()

@pytest.mark.asyncio
async def test_setup_queues_and_start_consuming_calls_consume(monkeypatch):
    c = make_consumer()
    await c.connect()
    q = await c.setup_queues()
    assert q is c.queue
    c.connection._closed = True
    await c.start_consuming()
    cb, no_ack = c.queue.consume_args
    assert cb == c.handle_request and no_ack is False

class FakeProcessCtx:
    def __init__(self, msg): self.msg = msg
    async def __aenter__(self): return self.msg
    async def __aexit__(self, *a): return False

class FakeIncomingMessage:
    def __init__(self, body_dict):
        self.body = json.dumps(body_dict).encode()
    def process(self, requeue=False):
        return FakeProcessCtx(self)

@pytest.mark.asyncio
async def test_handle_request_success_and_dedupe(monkeypatch):
    c = make_consumer()
    called = {}
    async def fake_route(method, ctx, ep, payload):
        called.update(dict(method=method, endpoint=ep, data=payload, ctx=ctx)); return {"ok":1}
    sent = {}
    async def fake_send(corr, resp): sent["corr"]=corr; sent["resp"]=resp
    monkeypatch.setattr(c, "_route_request", fake_route)
    monkeypatch.setattr(c, "_send_response", fake_send)
    msg = FakeIncomingMessage({"correlation_id":"c1","method":"GET","endpoint":"health","data":{"a":1},"user_context":{"u":1}})
    await c.handle_request(msg)
    assert sent["corr"] == "c1"
    assert sent["resp"]["status"] == "success" and sent["resp"]["data"]["ok"] == 1
    assert "c1" in c.processed_requests

    sent.clear()
    await c.handle_request(msg)
    assert sent == {}

@pytest.mark.asyncio
async def test_handle_request_routing_exception_sends_error(monkeypatch):
    c = make_consumer()
    async def boom(*a, **k): raise ValueError("bad route")
    out = {}
    async def fake_send(corr, resp): out["corr"]=corr; out["resp"]=resp
    monkeypatch.setattr(c, "_route_request", boom)
    monkeypatch.setattr(c, "_send_response", fake_send)
    msg = FakeIncomingMessage({"correlation_id":"c2","method":"GET","endpoint":"x","data":{}})
    await c.handle_request(msg)
    assert out["corr"] == "c2"
    assert out["resp"]["status"] == "error"
    assert out["resp"]["error"]["type"] == "ValueError" and "bad route" in out["resp"]["error"]["message"]


@pytest.mark.asyncio
async def test_route_request_validations():
    c = make_consumer()
    with pytest.raises(ValueError):
        await c._route_request(None, {}, "")
    with pytest.raises(ValueError):
        await c._route_request("GET", "ctx", "")
    with pytest.raises(ValueError):
        await c._route_request("GET", {}, None)


@pytest.mark.asyncio
@pytest.mark.parametrize("ep,handler,ret", [
    ("", "_handle_health_request", {"h":1}),
    ("health", "_handle_health_request", {"h":1}),
    ("vehicles/list", "_handle_vehicles_request", {"v":1}),
    ("daily-driver/today", "_handle_daily_driver_request", {"dd":1}),
    ("daily_driver/today", "_handle_daily_driver_request", {"dd":1}),
    ("drivers/all", "_handle_drivers_request", {"d":1}),
    ("assignments/all", "_handle_assignments_request", {"a":1}),
    ("vehicle-assignments/active", "_handle_assignments_request", {"a":1}),
    ("fuel/stats", "_handle_fuel_request", {"f":1}),
    ("mileage/update", "_handle_mileage_request", {"m":1}),
    ("notifications/list", "_handle_notifications_request", {"n":1}),
    ("analytics/summary", "_handle_analytics_request", {"an":1}),
    ("status", "_handle_status_request", {"s":1}),
    ("service-status", "_handle_status_request", {"s":1}),
    ("docs", "_handle_docs_request", {"doc":1}),
    ("openapi", "_handle_docs_request", {"doc":1}),
    ("metrics/live", "_handle_metrics_request", {"met":1}),
])
async def test_route_request_each_branch(monkeypatch, ep, handler, ret):
    c = make_consumer()
    async def fake(*a, **k): return ret
    monkeypatch.setattr(c, handler, fake)
    ctx = {"x":1}
    out = await c._route_request("GET", ctx, ep, {"p":2})
    assert out == ret
    assert ctx["endpoint"] == ep.strip("/").strip()
    assert ctx["data"] == {"p":2}

@pytest.mark.asyncio
async def test_route_request_unknown_endpoint_raises():
    c = make_consumer()
    with pytest.raises(ValueError):
        await c._route_request("GET", {}, "unknown", {})


def _install_service(mod_name, attr_name, ok=True, payload=None):
    mname = f"services.{mod_name}"
    mod = types.ModuleType(mname)
    class _S:
        async def handle_request(self, method, ctx):
            if not ok: raise RuntimeError("boom")
            return payload if payload is not None else {"ok": mod_name}
    setattr(mod, attr_name, _S())
    sys.modules[mname] = mod

@pytest.mark.asyncio
@pytest.mark.parametrize("mod,attr,method_name,error_key", [
    ("vehicle_service", "vehicle_service", "_handle_vehicles_request", "VehicleRequestError"),
    ("drivers_service", "drivers_service", "_handle_daily_driver_request", "DriversRequestError"),
    ("driver_service", "driver_service", "_handle_drivers_request", "DriverRequestError"),
    ("assignment_service", "assignment_service", "_handle_assignments_request", "AssignmentRequestError"),
    ("fuel_service", "fuel_service", "_handle_fuel_request", "FuelRequestError"),
    ("mileage_service", "mileage_service", "_handle_mileage_request", "MileageRequestError"),
    ("notification_service", "notification_service", "_handle_notifications_request", "NotificationRequestError"),
    ("analytics_service", "analytics_service", "_handle_analytics_request", "AnalyticsRequestError"),
])
async def test_handle_service_success_and_error(monkeypatch, mod, attr, method_name, error_key):
    c = make_consumer()
    _install_service(mod, attr, ok=True, payload={"ok":mod})
    fn = getattr(c, method_name)
    out = await fn("GET", {"endpoint":"x","data":{}})
    assert out == {"ok": mod}
    _install_service(mod, attr, ok=False)
    out2 = await fn("GET", {"endpoint":"x","data":{}})
    assert out2["status"] == "error" and out2["error"] == error_key


@pytest.mark.asyncio
async def test_health_status_docs_metrics():
    c = make_consumer()
    h = await c._handle_health_request("GET", {})
    assert h["status"] == "healthy" and h["service"] == "management"
    with pytest.raises(ValueError): await c._handle_health_request("POST", {})
    s = await c._handle_status_request("GET", {})
    assert s["status"] == "operational" and s["service"] == "management"
    with pytest.raises(ValueError): await c._handle_status_request("PUT", {})
    d = await c._handle_docs_request("GET", {})
    assert "openapi_url" in d
    with pytest.raises(ValueError): await c._handle_docs_request("PATCH", {})
    c.processed_requests = {"a","b","c"}
    m = await c._handle_metrics_request("GET", {})
    assert m["metrics"]["requests_processed"] == 3
    with pytest.raises(ValueError): await c._handle_metrics_request("DELETE", {})


@pytest.mark.asyncio
async def test_send_response_publishes_json():
    c = make_consumer()

    c.response_exchange = FakeExchange("resp.ex")
    c.config = RabbitMQConfig()
    payload = {"any":"thing"}
    await c._send_response("cid-1", payload)
    assert c.response_exchange.published, "no publish"
    msg, rk = c.response_exchange.published[-1]
    assert rk == c.config.ROUTING_KEYS["core_responses"]
    data = json.loads(msg.body.decode())
    assert data["correlation_id"] == "cid-1"
    assert data["status"] == "success"
    assert data["data"] == payload


@pytest.mark.asyncio
async def test_stop_consuming_closes_connection():
    c = make_consumer()
    await c.connect()
    assert c.connection.is_closed is False
    await c.stop_consuming()
    assert c.is_consuming is False and c.connection.is_closed is True
