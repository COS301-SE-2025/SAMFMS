import sys, os, types, importlib.util, pytest
from datetime import datetime, timedelta

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..", "services", "notification_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "management", "services", "notification_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "notification_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "services", "notification_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "notification_service.py")),
]

def _snapshot(names):
    return {n: sys.modules.get(n) for n in names}

def _restore(snapshot):
    for name, orig in snapshot.items():
        if orig is None:
            if name in sys.modules:
                del sys.modules[name]
        else:
            sys.modules[name] = orig

def _ensure(name, as_pkg=False):
    if name not in sys.modules:
        m = types.ModuleType(name)
        if as_pkg: m.__path__ = []
        sys.modules[name] = m
    return sys.modules[name]

def _install_stubs():

    bson_mod = _ensure("bson")
    class _ObjectId:
        def __init__(self, v): self.v = str(v)
        def __repr__(self): return f"OID({self.v})"
    bson_mod.ObjectId = _ObjectId


    schemas_pkg = _ensure("schemas", as_pkg=True)
    schemas_entities = _ensure("schemas.entities")

    class NotificationType:
        TRIP_STARTED = "TRIP_STARTED"
        TRIP_COMPLETED = "TRIP_COMPLETED"
        TRIP_DELAYED = "TRIP_DELAYED"
        DRIVER_LATE = "DRIVER_LATE"
        ROUTE_CHANGED = "ROUTE_CHANGED"
        TRAFFIC_ALERT = "TRAFFIC_ALERT"
        DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
        DRIVER_UNASSIGNED = "DRIVER_UNASSIGNED"
    schemas_entities.NotificationType = NotificationType

    class NotificationPreferences:
        def __init__(self, **data):
            self.trip_started = data.get("trip_started", True)
            self.trip_completed = data.get("trip_completed", True)
            self.trip_delayed = data.get("trip_delayed", True)
            self.driver_late = data.get("driver_late", True)
            self.route_changed = data.get("route_changed", True)
            self.traffic_alert = data.get("traffic_alert", True)
            self.driver_assigned = data.get("driver_assigned", True)
            self.driver_unassigned = data.get("driver_unassigned", True)
            self.email_enabled = data.get("email_enabled", True)
            self.push_enabled = data.get("push_enabled", True)
            self.sms_enabled = data.get("sms_enabled", True)
            self.email = data.get("email", "u@example.com")
            self.phone = data.get("phone", "+100000000")
            self.quiet_hours_start = data.get("quiet_hours_start")
            self.quiet_hours_end = data.get("quiet_hours_end")
            self.user_id = data.get("user_id")
            self.id = data.get("_id") or data.get("id")
        def dict(self): return dict(self.__dict__)
    schemas_entities.NotificationPreferences = NotificationPreferences

    class Notification:
        def __init__(self, **data):
            self.__dict__.update(data)
            if "_id" in data and "id" not in data:
                self.id = str(data["_id"])
        def dict(self): return dict(self.__dict__)
    schemas_entities.Notification = Notification

    class Trip:
        def __init__(self, **data):
            self.id = data.get("id")
            self.name = data.get("name")
            self.created_by = data.get("created_by")
            self.driver_assignment = data.get("driver_assignment")
    schemas_entities.Trip = Trip

    schemas_requests = _ensure("schemas.requests")
    class NotificationRequest:
        def __init__(self, **data):
            self.user_ids = data["user_ids"]
            self.type = data["type"]
            self.title = data["title"]
            self.message = data["message"]
            self.trip_id = data.get("trip_id")
            self.driver_id = data.get("driver_id")
            self.data = data.get("data")
            self.channels = data.get("channels", [])
            self.scheduled_for = data.get("scheduled_for")
        def dict(self): return dict(self.__dict__)
    schemas_requests.NotificationRequest = NotificationRequest

    class UpdateNotificationPreferencesRequest:
        def __init__(self, **data):
            self._data = dict(data)
            for k, v in data.items(): setattr(self, k, v)
        def dict(self, exclude_unset=False):
            if not exclude_unset: return dict(self._data)
            return {k: v for k, v in self._data.items() if v is not None}
    schemas_requests.UpdateNotificationPreferencesRequest = UpdateNotificationPreferencesRequest

    events_pkg = _ensure("events", as_pkg=True)
    events_pub = _ensure("events.publisher")
    class _EP:
        async def publish_event(self, evt): pass
    events_pub.event_publisher = _EP()


    repositories_pkg = _ensure("repositories", as_pkg=True)
    repositories_database = _ensure("repositories.database")

    class _InsertOne:
        def __init__(self, inserted_id): self.inserted_id = inserted_id
    class _UpdateResult:
        def __init__(self, modified): self.modified_count = modified

    class _AsyncCursor:
        def __init__(self, docs):
            self._docs = list(docs); self._skip = 0; self._limit = None
        def sort(self, key, direction):
            self._docs.sort(key=lambda d: d.get(key), reverse=(direction == -1)); return self
        def skip(self, n): self._skip = n; return self
        def limit(self, n): self._limit = n; return self
        def __aiter__(self): self._i = 0; return self
        async def __anext__(self):
            start = self._skip
            docs = self._docs[start:]
            if self._limit is not None: docs = docs[:self._limit]
            if self._i >= len(docs): raise StopAsyncIteration
            d = docs[self._i]; self._i += 1; return d

    class _Notifications:
        def __init__(self):
            self.docs = {}; self.next = 1
            self.raise_on_insert = None
            self.raise_on_update = None
            self.raise_on_count = None
        async def insert_one(self, data):
            if self.raise_on_insert: raise self.raise_on_insert
            _id = f"n{self.next}"; self.next += 1
            self.docs[_id] = {"_id": _id, **data}
            return _InsertOne(_id)
        async def update_one(self, filt, update):
            if self.raise_on_update: raise self.raise_on_update
            key = getattr(filt.get("_id"), "v", filt.get("_id")); key = str(key)
            uid = filt.get("user_id")
            if key not in self.docs: return _UpdateResult(0)
            if uid is not None and self.docs[key].get("user_id") != uid:
                return _UpdateResult(0)
            if "$set" in update: self.docs[key].update(update["$set"])
            return _UpdateResult(1)
        def find(self, query):
            def _m(doc, q): return all(doc.get(k) == v for k, v in q.items())
            return _AsyncCursor([dict(v) for v in self.docs.values() if _m(v, query)])
        async def count_documents(self, query):
            if self.raise_on_count: raise self.raise_on_count
            return sum(1 for v in self.docs.values() if all(v.get(k) == val for k, val in query.items()))

    class _Prefs:
        def __init__(self):
            self.docs = {}
            self.raise_on_find = None
            self.raise_on_update = None
            self.raise_on_insert = None
        async def find_one(self, query):
            if self.raise_on_find: raise self.raise_on_find
            uid = query.get("user_id"); d = self.docs.get(uid)
            return dict(d) if d else None
        async def update_one(self, filt, update):
            if self.raise_on_update: raise self.raise_on_update
            uid = filt.get("user_id")
            if uid not in self.docs: return _UpdateResult(0)
            if "$set" in update: self.docs[uid].update(update["$set"])
            return _UpdateResult(1)
        async def insert_one(self, data):
            if self.raise_on_insert: raise self.raise_on_insert
            uid = data.get("user_id")
            self.docs[uid] = {"_id": f"p_{uid}", **data}
            return _InsertOne(self.docs[uid]["_id"])

    class _DB:
        def __init__(self):
            self.notifications = _Notifications()
            self.notification_preferences = _Prefs()

    repositories_database.db_manager = _DB()

    return {
        "NotificationType": NotificationType,
        "NotificationPreferences": NotificationPreferences,
        "Notification": Notification,
        "NotificationRequest": NotificationRequest,
        "UpdateNotificationPreferencesRequest": UpdateNotificationPreferencesRequest,
        "Trip": Trip,
    }

def _load_service_isolated():
    names = [
        "repositories", "repositories.database",
        "schemas", "schemas.entities", "schemas.requests",
        "events", "events.publisher",
        "bson",
        "services.notification_service",
    ]
    snap = _snapshot(names)
    local_types = _install_stubs()

    for p in CANDIDATES:
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("services.notification_service", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.notification_service"] = mod
            spec.loader.exec_module(mod)

            svc_cls = mod.NotificationService
            db = mod.db_manager
            _restore(snap)  
            return mod, svc_cls, local_types, db
    _restore(snap)
    raise ImportError("notification_service.py not found")

# ----------------- Tests -----------------

@pytest.mark.asyncio
async def test_send_notification_skips_by_prefs_quiet_hours_and_sends_default(monkeypatch):
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()

    db.notification_preferences.docs["u1"] = {"_id":"p_u1","user_id":"u1","trip_started":False,
                                              "email_enabled":True,"push_enabled":True,"sms_enabled":True}

    db.notification_preferences.docs["u2"] = {"_id":"p_u2","user_id":"u2","trip_started":True,
                                              "quiet_hours_start":"00:00","quiet_hours_end":"23:59",
                                              "email_enabled":True,"push_enabled":True,"sms_enabled":True}
    req = T["NotificationRequest"](
        user_ids=["u1","u2","u3"],
        type=T["NotificationType"].TRIP_STARTED,
        title="t", message="m",
        trip_id="T1", driver_id="D1",
        channels=["email","push"]
    )
    async def noop(notification, prefs): pass
    monkeypatch.setattr(svc, "_deliver_notification", noop, raising=True)
    out = await svc.send_notification(req)
    assert [n.user_id for n in out] == ["u3"]
    stored = [v for v in db.notifications.docs.values() if v["user_id"]=="u3"]
    assert stored and set(stored[0]["channels"]) == {"email","push"}

@pytest.mark.asyncio
async def test_send_notification_channels_filtered_and_delivery_status(monkeypatch):
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()

    db.notification_preferences.docs["u4"] = {"_id":"p_u4","user_id":"u4",
                                              "email_enabled":True,"push_enabled":False,"sms_enabled":False}
    req = T["NotificationRequest"](
        user_ids=["u4"], type=T["NotificationType"].TRIP_COMPLETED,
        title="done", message="ok", trip_id="T2", driver_id=None,
        channels=["email","push","sms"],
        scheduled_for=datetime(2025,1,1,12,0,0)
    )
    async def send_email(notification, prefs): return True
    async def send_push(notification): return False
    async def send_sms(notification, prefs): return True
    monkeypatch.setattr(svc, "_send_email", send_email, raising=True)
    monkeypatch.setattr(svc, "_send_push", send_push, raising=True)
    monkeypatch.setattr(svc, "_send_sms", send_sms, raising=True)
    out = await svc.send_notification(req)
    assert len(out) == 1
    nid = out[0].id
    doc = db.notifications.docs[nid]
    assert doc["sent_at"] == datetime(2025,1,1,12,0,0)

    ds = doc.get("delivery_status")
    assert ds is None or ds == {"email": "sent"}

@pytest.mark.asyncio
async def test_send_notification_insert_error_propagates():
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    db.notification_preferences.docs["u5"] = {"_id":"p_u5","user_id":"u5"}
    db.notifications.raise_on_insert = RuntimeError("insert fail")
    req = T["NotificationRequest"](
        user_ids=["u5"], type=T["NotificationType"].TRIP_DELAYED,
        title="d", message="m", trip_id="T3", driver_id=None, channels=["push"]
    )
    with pytest.raises(RuntimeError):
        await svc.send_notification(req)

@pytest.mark.asyncio
async def test_get_user_notifications_unread_and_paging_and_error(monkeypatch):
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    for i, read in enumerate([False, True, False]):
        await db.notifications.insert_one({"user_id":"u6","is_read":read,"title":f"n{i}","sent_at": datetime(2025,1,1,12,0,0)+timedelta(minutes=i)})
    items, total = await svc.get_user_notifications("u6", unread_only=True, limit=10, skip=0)
    assert total == 2 and all(not n.is_read for n in items)
    items2, total2 = await svc.get_user_notifications("u6", unread_only=False, limit=2, skip=0)
    assert total2 == 3 and len(items2) == 2 and items2[0].title == "n2"
    old_find = db.notifications.find
    def boom(_): raise RuntimeError("find fail")
    db.notifications.find = boom
    with pytest.raises(RuntimeError):
        await svc.get_user_notifications("u6")
    db.notifications.find = old_find

@pytest.mark.asyncio
async def test_mark_notification_read_true_false_and_error():
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    ins = await db.notifications.insert_one({"user_id":"u7","is_read":False,"title":"x","sent_at":datetime.utcnow()})
    ok = await svc.mark_notification_read(ins.inserted_id, "u7")
    assert ok is True and db.notifications.docs[ins.inserted_id]["is_read"] is True
    ok2 = await svc.mark_notification_read(ins.inserted_id, "someoneelse")
    assert ok2 is False
    db.notifications.raise_on_update = RuntimeError("update fail")
    with pytest.raises(RuntimeError):
        await svc.mark_notification_read(ins.inserted_id, "u7")

@pytest.mark.asyncio
async def test_get_unread_count_success_and_error():
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    await db.notifications.insert_one({"user_id":"u8","is_read":False,"title":"a","sent_at":datetime.utcnow()})
    await db.notifications.insert_one({"user_id":"u8","is_read":True,"title":"b","sent_at":datetime.utcnow()})
    assert await svc.get_unread_count("u8") == 1
    db.notifications.raise_on_count = RuntimeError("count fail")
    assert await svc.get_unread_count("u8") == 0

@pytest.mark.asyncio
async def test_get_and_update_user_preferences_variants_and_errors():
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    assert await svc.get_user_preferences("u9") is None
    req = T["UpdateNotificationPreferencesRequest"](email_enabled=True, push_enabled=False, sms_enabled=False,
                                                    quiet_hours_start="22:00", quiet_hours_end="06:00")
    updated = await svc.update_user_preferences("u9", req)
    assert updated.user_id == "u9"
    req2 = T["UpdateNotificationPreferencesRequest"](push_enabled=True)
    updated2 = await svc.update_user_preferences("u9", req2)
    assert updated2.push_enabled is True

    db.notification_preferences.raise_on_find = RuntimeError("find err")
    assert await svc.get_user_preferences("u9") is None
    db.notification_preferences.raise_on_find = None

    db.notification_preferences.raise_on_update = RuntimeError("upd err")
    with pytest.raises(RuntimeError):
        await svc.update_user_preferences("u9", T["UpdateNotificationPreferencesRequest"](push_enabled=False))

@pytest.mark.asyncio
async def test_trip_notifications_call_send_and_swallow_errors(monkeypatch):
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    trip = T["Trip"](id="T10", name="Trip X", created_by="creator", driver_assignment="driver1")
    called = {"n": 0}
    async def spy(req): called["n"] += 1
    monkeypatch.setattr(svc, "send_notification", spy, raising=True)
    await svc.notify_trip_started(trip)
    await svc.notify_trip_completed(trip)
    await svc.notify_trip_delayed(trip, 15)
    await svc.notify_driver_assigned(trip, "driver2")
    await svc.notify_route_changed(trip, "detour")
    assert called["n"] == 5
    async def boom(req): raise RuntimeError("explode")
    monkeypatch.setattr(svc, "send_notification", boom, raising=True)
    await svc.notify_trip_started(trip) 

def test_should_send_notification_mapping_and_defaults():
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    P = T["NotificationPreferences"]
    N = T["NotificationType"]
    prefs = P(trip_started=False, trip_completed=True, trip_delayed=False,
              driver_late=True, route_changed=False, traffic_alert=True,
              driver_assigned=False, driver_unassigned=True)
    assert svc._should_send_notification(N.TRIP_STARTED, prefs) is False
    assert svc._should_send_notification(N.TRIP_COMPLETED, prefs) is True
    assert svc._should_send_notification(N.TRIP_DELAYED, prefs) is False
    assert svc._should_send_notification("UNKNOWN", prefs) is True
    assert svc._should_send_notification(N.TRIP_STARTED, None) is True

def test_is_quiet_hours_true_and_false():
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    P = T["NotificationPreferences"]
    assert svc._is_quiet_hours(P(quiet_hours_start="00:00", quiet_hours_end="23:59")) is True
    assert svc._is_quiet_hours(P()) is False
    assert svc._is_quiet_hours(P(quiet_hours_start="23:59", quiet_hours_end="00:01")) is False

def test_get_enabled_channels_variants_and_fallback():
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    P = T["NotificationPreferences"]
    assert svc._get_enabled_channels(["email","push","sms"], P(email_enabled=True, push_enabled=False, sms_enabled=False)) == ["email"]
    assert svc._get_enabled_channels(["push"], P(email_enabled=False, push_enabled=False, sms_enabled=False)) == ["push"]
    assert set(svc._get_enabled_channels(["email","push"], None)) == {"email","push"}

@pytest.mark.asyncio
async def test__deliver_notification_status_and_resilience(monkeypatch):
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    ins = await db.notifications.insert_one({"user_id":"u11","title":"hello","channels":["email","push","sms"],"sent_at":datetime.utcnow()})
    notif = T["Notification"](_id=ins.inserted_id, id=ins.inserted_id, user_id="u11", title="hello", channels=["email","push","sms"])
    async def ok_email(n, p): return True
    async def bad_push(n): raise RuntimeError("push down")
    async def ok_sms(n, p): return False
    monkeypatch.setattr(svc, "_send_email", ok_email, raising=True)
    monkeypatch.setattr(svc, "_send_push", bad_push, raising=True)
    monkeypatch.setattr(svc, "_send_sms", ok_sms, raising=True)
    await svc._deliver_notification(notif, None) 
    doc = db.notifications.docs.get(ins.inserted_id, {})
    if "delivery_status" in doc:
        assert set(doc["delivery_status"].keys()) <= {"email","push","sms"}

@pytest.mark.asyncio
async def test_get_trip_notification_recipients_unique():
    ns_mod, Service, T, db = _load_service_isolated()
    svc = Service()
    trip = T["Trip"](id="T12", name="n", created_by="u1", driver_assignment="u1")
    recips = await svc._get_trip_notification_recipients(trip)
    assert recips == ["u1"]
