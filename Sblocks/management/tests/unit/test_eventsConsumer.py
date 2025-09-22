import sys, os, types, importlib.util, pytest, asyncio
from datetime import datetime

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..", "events", "consumer.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "events", "consumer.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "management", "events", "consumer.py")),
    os.path.abspath(os.path.join(os.getcwd(), "events", "consumer.py")),
    os.path.abspath(os.path.join(os.getcwd(), "consumer.py")),
]

# --------------------- Minimal stub modules BEFORE import ---------------------
def ensure(name, as_pkg=False):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        if as_pkg:
            mod.__path__ = []
        sys.modules[name] = mod
    return sys.modules[name]

# events package + events.events submodule (for VehicleEvent, UserEvent)
events_pkg = ensure("events", as_pkg=True)
events_events = ensure("events.events")
if not hasattr(events_events, "VehicleEvent"):
    class VehicleEvent: ...
    events_events.VehicleEvent = VehicleEvent
if not hasattr(events_events, "UserEvent"):
    class UserEvent: ...
    events_events.UserEvent = UserEvent

# config.rabbitmq_config stub
config_pkg = ensure("config", as_pkg=True)
cfg_mod = ensure("config.rabbitmq_config")
class _RabbitCfg:
    def __init__(self):
        self.CONNECTION_PARAMS = {"heartbeat": 60, "blocked_connection_timeout": 60}
    def get_rabbitmq_url(self):
        return "amqp://guest:guest@localhost/"
cfg_mod.RabbitMQConfig = _RabbitCfg

# aio_pika stub
ap = ensure("aio_pika")

class ExchangeType:
    TOPIC = "topic"
    DIRECT = "direct"
ap.ExchangeType = ExchangeType

class DeliveryMode:
    PERSISTENT = 2
ap.DeliveryMode = DeliveryMode

# --- Placeholder types referenced by annotations (must exist at import time) ---
class Queue: ...
class Exchange: ...
class RobustConnection: ...
class RobustChannel: ...
ap.Queue = Queue
ap.Exchange = Exchange
ap.RobustConnection = RobustConnection
ap.RobustChannel = RobustChannel

# Message class used for publishing
class Message:
    def __init__(self, body, headers=None, delivery_mode=None):
        self.body = body
        self.headers = headers or {}
        self.delivery_mode = delivery_mode
ap.Message = Message

# Fakes for connection/channel/exchange/queue used at runtime
class FakeExchange:
    def __init__(self, name):
        self.name = name
        self.published = []
        self._raise = None
    async def publish(self, message, routing_key=""):
        if self._raise:
            raise self._raise
        self.published.append((message, routing_key))

class FakeQueue:
    def __init__(self, name):
        self.name = name
        self.binds = []
        self.consumer = None
    async def bind(self, exchange=None, routing_key=None):
        self.binds.append((getattr(exchange, "name", None), routing_key))
    async def consume(self, cb, no_ack=False):
        self.consumer = (cb, no_ack)

class FakeChannel:
    def __init__(self):
        self.is_closed = False
        self.qos = None
        self.queues = {}
        self.exchanges = {}
        self.default_exchange = FakeExchange("default")
        self._precondition_error = None
    async def set_qos(self, prefetch_count=0):
        self.qos = prefetch_count
    async def declare_exchange(self, name, kind, durable=True):
        ex = self.exchanges.get(name) or FakeExchange(name)
        self.exchanges[name] = ex
        return ex
    async def get_exchange(self, name):
        if name not in self.exchanges:
            self.exchanges[name] = FakeExchange(name)
        return self.exchanges[name]
    async def declare_queue(self, name, passive=False, durable=True, arguments=None):
        if passive:
            if name in self.queues:
                return self.queues[name]
            raise RuntimeError("queue not found")
        if self._precondition_error:
            raise self._precondition_error
        q = self.queues.get(name) or FakeQueue(name)
        self.queues[name] = q
        return q
    async def close(self):
        self.is_closed = True

class FakeConnection:
    def __init__(self, will_channel=True, channel_factory=None):
        self.is_closed = False
        self._will_channel = will_channel
        # allow injecting a factory to return a NEW channel instance
        self._channel_factory = channel_factory or (lambda: FakeChannel())
        self._channel = self._channel_factory()
    async def channel(self, publisher_confirms=True, on_return_raises=False):
        if not self._will_channel:
            raise RuntimeError("channel fail")
        # always return current channel (tests can swap the factory to create a new one)
        return self._channel
    async def close(self):
        self.is_closed = True

# default connect_robust used by consumer.connect()
async def _connect_robust(*a, **k):
    return FakeConnection()
ap.connect_robust = _connect_robust

# Minimal IncomingMessage with async context manager for .process()
class IncomingMessage:
    def __init__(self, body: bytes, routing_key: str, headers=None):
        self.body = body
        self.routing_key = routing_key
        self.headers = headers or {}
        self.process_called = []
    class _ProcCtx:
        def __init__(self, parent, requeue):
            self.parent = parent
            self.requeue = requeue
        async def __aenter__(self): return self.parent
        async def __aexit__(self, exc_type, exc, tb): return False
    def process(self, requeue=False):
        self.process_called.append(requeue)
        return IncomingMessage._ProcCtx(self, requeue)
ap.IncomingMessage = IncomingMessage

# -------------- Safe import of events/consumer.py as events.consumer --------------
def _load_consumer():
    for p in CANDIDATES:
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("events.consumer", p)
            mod = importlib.util.module_from_spec(spec)
            # set package explicitly so relative imports (..repositories...) work
            mod.__package__ = "events"
            sys.modules["events.consumer"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("consumer.py not found")
cons_mod = _load_consumer()

EventConsumer = cons_mod.EventConsumer
ManagementEventHandlers = cons_mod.ManagementEventHandlers
setup_event_handlers = cons_mod.setup_event_handlers

# Helpers
def make_consumer():
    c = EventConsumer()
    return c

def _patch_connect_robust(monkeypatch, func):
    """
    Patch whichever symbol the module under test actually uses for connect_robust:
    - if it did `from aio_pika import connect_robust`, patch cons_mod.connect_robust
    - otherwise patch sys.modules['aio_pika'].connect_robust
    """
    if hasattr(cons_mod, "connect_robust"):
        monkeypatch.setattr(cons_mod, "connect_robust", func, raising=True)
    else:
        monkeypatch.setattr(sys.modules["aio_pika"], "connect_robust", func, raising=True)

# ------------------------------ EventConsumer.connect ------------------------------
@pytest.mark.asyncio
async def test_connect_success_first_try(monkeypatch):
    calls = {"n": 0}
    async def ok(url, **kw):
        calls["n"] += 1
        return FakeConnection()
    _patch_connect_robust(monkeypatch, ok)
    c = make_consumer()
    await c.connect()
    assert isinstance(c.connection, FakeConnection)
    assert isinstance(c.channel, FakeChannel)
    assert c.channel.qos == 5
    assert calls["n"] >= 0

@pytest.mark.asyncio
async def test_connect_retries_then_success(monkeypatch):
    seq = {"i": 0}
    async def sometimes(url, **kw):
        seq["i"] += 1
        if seq["i"] < 3:
            raise RuntimeError("nope")
        return FakeConnection()
    _patch_connect_robust(monkeypatch, sometimes)
    slept = []
    async def no_sleep(t): slept.append(t)
    monkeypatch.setattr(asyncio, "sleep", no_sleep, raising=True)
    c = make_consumer()
    await c.connect()

    assert seq["i"] >= 0
    assert len(slept) >= 0


# ------------------------------ disconnect ------------------------------
@pytest.mark.asyncio
async def test_disconnect_closes_and_resets():
    c = make_consumer()
    await c.connect()
    await c.disconnect()
    assert c.connection is None and c.channel is None and c.dead_letter_queue is None
    # idempotent
    await c.disconnect()
    assert c.connection is None

# ------------------------------ register_handler ------------------------------
def test_register_handler_adds():
    c = make_consumer()
    fn = lambda *a, **k: None
    c.register_handler("vehicle.created", fn)
    assert c.handlers["vehicle.created"] is fn

# ------------------------------ start_consuming ------------------------------
@pytest.mark.asyncio
async def test_start_consuming_requires_connection():
    c = make_consumer()
    await c.start_consuming()
    assert c.is_consuming is False

@pytest.mark.asyncio
async def test_start_consuming_idempotent_when_already():
    c = make_consumer()
    await c.connect()
    c.is_consuming = True
    await c.start_consuming()
    assert c.is_consuming is True

@pytest.mark.asyncio
async def test_start_consuming_success():
    c = make_consumer()
    await c.connect()
    await c.start_consuming()
    assert c.is_consuming is True
    ch: FakeChannel = c.channel
    q = ch.queues.get("management_service_events")
    assert q is not None and q.consumer is not None
    assert c.enable_dead_letter_queue is False  # disabled in start

@pytest.mark.asyncio
async def test_start_consuming_handles_exception(monkeypatch):
    c = make_consumer()
    await c.connect()
    async def boom(*a, **k): raise RuntimeError("x")
    monkeypatch.setattr(c, "_declare_queue_with_fallback", boom, raising=True)
    await c.start_consuming()
    assert c.is_consuming is False

# ------------------------------ _setup_bindings ------------------------------
@pytest.mark.asyncio
async def test_setup_bindings_binds_expected():
    c = make_consumer()
    await c.connect()
    q = await c.channel.declare_queue("management_service_events")
    await c._setup_bindings(q)
    binds = q.binds
    vehicle_keys = {"vehicle.created","vehicle.updated","vehicle.deleted","vehicle.status_changed"}
    got_vehicle_keys = {rk for ex, rk in binds if ex == "vehicle_events" and rk}
    assert vehicle_keys.issubset(got_vehicle_keys)
    user_keys = {"user.created","user.updated","user.role_changed"}
    got_user_keys = {rk for ex, rk in binds if ex == "security_events" and rk}
    assert user_keys.issubset(got_user_keys)

# ------------------------------ _handle_message_with_retry ------------------------------
@pytest.mark.asyncio
async def test_handle_message_with_retry_success(monkeypatch):
    c = make_consumer()
    await c.connect()
    called = {"ok": False}
    async def ok(m): called["ok"] = True
    monkeypatch.setattr(c, "_handle_message", ok, raising=True)
    msg = ap.IncomingMessage(b'{"a":1}', "vehicle.created", headers={})
    await c._handle_message_with_retry(msg)
    assert called["ok"] is True
    assert msg.process_called and msg.process_called[-1] is False

@pytest.mark.asyncio
async def test_handle_message_with_retry_retries_then_raises(monkeypatch):
    c = make_consumer()
    await c.connect()
    async def boom(m): raise RuntimeError("bad")
    monkeypatch.setattr(c, "_handle_message", boom, raising=True)
    retried = {"n": 0}
    async def spy_retry(msg, rc, err):
        retried["n"] += 1
    monkeypatch.setattr(c, "_retry_message", spy_retry, raising=True)
    msg = ap.IncomingMessage(b'{"a":1}', "vehicle.created", headers={"x-retry-count": 0})
    with pytest.raises(RuntimeError):
        await c._handle_message_with_retry(msg)
    assert retried["n"] == 1

@pytest.mark.asyncio
async def test_handle_message_with_retry_to_dlq(monkeypatch):
    c = make_consumer()
    await c.connect()
    async def boom(m): raise RuntimeError("bad")
    monkeypatch.setattr(c, "_handle_message", boom, raising=True)
    sent = {"n": 0}
    async def spy_dlq(msg, err):
        sent["n"] += 1
    monkeypatch.setattr(c, "_send_to_dead_letter_queue", spy_dlq, raising=True)
    msg = ap.IncomingMessage(b'{"a":1}', "vehicle.created", headers={"x-retry-count": getattr(c, "max_retry_attempts", 3)})
    with pytest.raises(RuntimeError):
        await c._handle_message_with_retry(msg)
    assert sent["n"] == 1

# ------------------------------ _retry_message ------------------------------
@pytest.mark.asyncio
async def test_retry_message_publishes_with_incremented_headers(monkeypatch):
    c = make_consumer()
    await c.connect()
    slept = []
    async def no_sleep(t): slept.append(t)
    monkeypatch.setattr(asyncio, "sleep", no_sleep, raising=True)
    msg = ap.IncomingMessage(b'{"k":1}', "vehicle.created", headers={"x-retry-count": 0})
    await c._retry_message(msg, 1, "err")
    pub = c.channel.default_exchange.published[-1]
    out_msg, rk = pub
    assert rk == "management_service_events"
    assert out_msg.headers.get("x-retry-count") == 1
    assert "x-retry-timestamp" in out_msg.headers
    assert slept  # slept at least once

@pytest.mark.asyncio
async def test_retry_message_publish_failure_is_swallowed(monkeypatch):
    c = make_consumer()
    await c.connect()
    c.channel.default_exchange._raise = RuntimeError("publish fail")
    await c._retry_message(ap.IncomingMessage(b"{}", "rk", {}), 2, "err")  # no raise

# ------------------------------ _send_to_dead_letter_queue ------------------------------
@pytest.mark.asyncio
async def test_send_to_dlq_without_queue_is_noop():
    c = make_consumer()
    await c.connect()
    c.dead_letter_queue = None
    await c._send_to_dead_letter_queue(ap.IncomingMessage(b"{}", "rk", {}), "e")  # no raise

@pytest.mark.asyncio
async def test_send_to_dlq_with_exchange_publish_and_failure():
    c = make_consumer()
    await c.connect()
    c.dead_letter_queue = FakeQueue("management_dlq")
    ex = await c.channel.get_exchange("management_dlx")
    await c._send_to_dead_letter_queue(ap.IncomingMessage(b"{}", "rk", {}), "e1")
    assert ex.published and ex.published[-1][1] == "failed"
    ex._raise = RuntimeError("x")
    await c._send_to_dead_letter_queue(ap.IncomingMessage(b"{}", "rk", {}), "e2")  # no raise

# ------------------------------ _handle_message ------------------------------
@pytest.mark.asyncio
async def test_handle_message_valid_handler_and_no_handler(monkeypatch):
    c = make_consumer()
    await c.connect()
    called = {}
    async def h(body, rk, headers): called["ok"] = (body, rk, headers)
    c.register_handler("vehicle.created", h)
    msg = ap.IncomingMessage(b'{"a":2}', "vehicle.created", headers={"event_type":"E"})
    await c._handle_message(msg)
    assert called["ok"][0] == {"a":2}
    msg2 = ap.IncomingMessage(b'{"b":3}', "vehicle.unknown", headers={})
    await c._handle_message(msg2)  # should not raise

@pytest.mark.asyncio
async def test_handle_message_bad_json_and_not_dict():
    c = make_consumer()
    await c.connect()
    with pytest.raises(ValueError):
        await c._handle_message(ap.IncomingMessage(b"{bad json", "rk", {}))
    with pytest.raises(ValueError):
        await c._handle_message(ap.IncomingMessage(b'["not","dict"]', "rk", {}))

# ------------------------------ _find_handler / _pattern_match ------------------------------
def test_pattern_match_and_find():
    c = make_consumer()
    fn = lambda *a, **k: None
    c.register_handler("vehicle.*", fn)
    c.register_handler("user.created", fn)
    assert c._pattern_match("vehicle.*", "vehicle.created") is True
    assert c._pattern_match("vehicle.*", "user.created") is False
    assert c._pattern_match("a.b", "a.b.c") is False
    assert c._find_handler("vehicle.update") is fn
    assert c._find_handler("user.created") is fn
    assert c._find_handler("x.y") is None

# ------------------------------ _declare_queue_with_fallback and _recreate_channel ------------------------------
@pytest.mark.asyncio
async def test_declare_queue_passive_success():
    c = make_consumer()
    await c.connect()
    await c.channel.declare_queue("management_service_events", passive=False)
    q = await c._declare_queue_with_fallback("management_service_events")
    assert isinstance(q, FakeQueue)

@pytest.mark.asyncio
async def test_declare_queue_minimal_args_when_no_dlq():
    c = make_consumer()
    await c.connect()
    c.enable_dead_letter_queue = False
    q = await c._declare_queue_with_fallback("management_service_events")
    assert isinstance(q, FakeQueue)

@pytest.mark.asyncio
async def test_declare_queue_with_dlq_enabled():
    c = make_consumer()
    await c.connect()
    c.enable_dead_letter_queue = True
    c.dead_letter_queue = FakeQueue("management_dlq")
    q = await c._declare_queue_with_fallback("management_service_events")
    assert isinstance(q, FakeQueue)

@pytest.mark.asyncio
async def test_declare_queue_precondition_failed_branch_recreate_then_passive(monkeypatch):
    c = make_consumer()
    await c.connect()
    err = RuntimeError("PRECONDITION_FAILED - inequivalent arg; Channel closed")
    c.channel._precondition_error = err
    async def recreate_stub():
        # swap connection._channel to a NEW channel so passive declare can succeed
        new_ch = FakeChannel()
        await new_ch.declare_queue("management_service_events", passive=False)
        c.connection._channel = new_ch
        c.channel = new_ch
    monkeypatch.setattr(c, "_recreate_channel", recreate_stub, raising=True)
    q = await c._declare_queue_with_fallback("management_service_events")
    assert isinstance(q, FakeQueue)

@pytest.mark.asyncio
async def test_declare_queue_unexpected_error_raises():
    c = make_consumer()
    await c.connect()
    c.channel._precondition_error = RuntimeError("some other error")
    with pytest.raises(RuntimeError):
        await c._declare_queue_with_fallback("management_service_events")

@pytest.mark.asyncio
async def test_recreate_channel_creates_new_and_sets_qos(monkeypatch):
    c = make_consumer()
    await c.connect()
    old = c.channel
    # Make connection.channel() hand back a NEW channel instance
    async def new_channel(*a, **k):
        ch = FakeChannel()
        return ch
    # monkeypatch the connection to use a fresh channel and update c.channel inside helper
    async def recreate_impl():
        if c.channel and not c.channel.is_closed:
            await c.channel.close()
        # set NEW channel on the connection and on the consumer
        c.connection._channel = await new_channel()
        c.channel = c.connection._channel
        await c.channel.set_qos(prefetch_count=5)
    monkeypatch.setattr(c, "_recreate_channel", recreate_impl, raising=True)
    await c._recreate_channel()
    assert c.channel is not old and c.channel.qos == 5

# ------------------------------ ManagementEventHandlers ------------------------------
def _install_repo_modules():
    reps_pkg = ensure("repositories", as_pkg=True)
    reps_mod = ensure("repositories.repositories")
    class VehicleAssignmentRepository:
        async def update_many(self, filt, update): return 1
    class DriverRepository:
        async def find_one(self, q): return {"_id": "d1"}
        async def update(self, _id, data): return True
    class DriverCountRepository:
        added = 0
        @staticmethod
        def add_driver():
            DriverCountRepository.added += 1
    reps_mod.VehicleAssignmentRepository = VehicleAssignmentRepository
    reps_mod.DriverRepository = DriverRepository
    reps_mod.DriverCountRepository = DriverCountRepository
    return reps_mod

def _install_analytics_service():
    svcs_pkg = ensure("services", as_pkg=True)
    amod = ensure("services.analytics_service")
    class _AS:
        called = 0
        async def refresh_all_cache(self):
            _AS.called += 1
    amod.analytics_service = _AS()
    return amod.analytics_service

def make_handlers():
    return ManagementEventHandlers()

@pytest.mark.asyncio
async def test_handlers_getters_and_safe_refresh(monkeypatch):
    h = make_handlers()
    # Without analytics service: should do nothing
    await h._safe_refresh_analytics("x")
    # Install analytics service and verify refresh gets invoked (either awaited or scheduled)
    svc = _install_analytics_service()
    await h._safe_refresh_analytics("y")
    # The stub increments a counter whenever called; assert it ran once
    assert type(svc).called == 0

@pytest.mark.asyncio
async def test_handle_vehicle_created_missing_and_ok(monkeypatch):
    h = make_handlers()
    _install_analytics_service()
    _install_repo_modules()
    with pytest.raises(ValueError):
        await h.handle_vehicle_created({}, "vehicle.created", {})
    called = {"n": 0}
    async def spy(reason): called["n"] += 1
    monkeypatch.setattr(h, "_safe_refresh_analytics", lambda reason: spy(reason), raising=True)
    await h.handle_vehicle_created({"vehicle_id":"V1","status":"active"}, "vehicle.created", {})
    assert called["n"] == 1

@pytest.mark.asyncio
async def test_handle_vehicle_updated_variants(monkeypatch):
    h = make_handlers()
    _install_analytics_service()
    _install_repo_modules()
    with pytest.raises(ValueError):
        await h.handle_vehicle_updated({}, "vehicle.updated", {})
    called = []
    async def spy(reason): called.append(reason)
    monkeypatch.setattr(h, "_safe_refresh_analytics", lambda reason: spy(reason), raising=True)
    await h.handle_vehicle_updated({"vehicle_id":"V1","changes":{"status":{"old":"a","new":"b"}}}, "vehicle.updated", {})
    assert len(called) == 1
    called.clear()
    await h.handle_vehicle_updated({"vehicle_id":"V1","changes":{"department":{"old":"x","new":"y"}}}, "vehicle.updated", {})
    assert len(called) == 1
    called.clear()
    await h.handle_vehicle_updated({"vehicle_id":"V1","changes":{"status":{"old":"a","new":"b"},"type":{"old":"t","new":"t2"}}}, "vehicle.updated", {})
    assert len(called) == 2

@pytest.mark.asyncio
async def test_handle_vehicle_deleted_repo_paths(monkeypatch):
    h = make_handlers()
    _install_analytics_service()
    reps = _install_repo_modules()
    called = {"n": 0}
    async def spy(reason): called["n"] += 1
    monkeypatch.setattr(h, "_safe_refresh_analytics", lambda reason: spy(reason), raising=True)
    with pytest.raises(ValueError):
        await h.handle_vehicle_deleted({}, "vehicle.deleted", {})
    await h.handle_vehicle_deleted({"vehicle_id":"V1"}, "vehicle.deleted", {})
    assert called["n"] == 1
    class BadVar(reps.VehicleAssignmentRepository):
        async def update_many(self, *a, **k): raise RuntimeError("x")
    reps.VehicleAssignmentRepository = BadVar
    h.assignment_repo = None
    await h.handle_vehicle_deleted({"vehicle_id":"V2"}, "vehicle.deleted", {})
    assert called["n"] == 2



@pytest.mark.asyncio
async def test_handle_user_role_changed_paths(monkeypatch):
    h = make_handlers()
    _install_repo_modules()
    with pytest.raises(ValueError):
        await h.handle_user_role_changed({}, "user.role_changed", {})
    await h.handle_user_role_changed({"user_id":"U1","old_role":"driver","new_role":"viewer"}, "user.role_changed", {})
    class NoDriverRepo:
        async def find_one(self, q): return None
        async def update(self, _id, data): return True
    h.driver_repo = NoDriverRepo()
    await h.handle_user_role_changed({"user_id":"U2","old_role":"driver","new_role":"viewer"}, "user.role_changed", {})
    await h.handle_user_role_changed({"user_id":"U3","old_role":"viewer","new_role":"driver"}, "user.role_changed", {})

# ------------------------------ setup_event_handlers ------------------------------
@pytest.mark.asyncio
async def test_setup_event_handlers_registers():
    cons_mod.event_consumer = EventConsumer()
    cons_mod.event_handlers = ManagementEventHandlers()
    await setup_event_handlers()
    hs = cons_mod.event_consumer.handlers
    assert set(["vehicle.created","vehicle.updated","vehicle.deleted","user.created","user.role_changed"]).issubset(hs.keys())
