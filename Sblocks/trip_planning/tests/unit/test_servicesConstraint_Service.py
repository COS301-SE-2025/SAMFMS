import sys, os, types, importlib.util, pytest
from datetime import datetime

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..", "services", "constraint_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "management", "services", "constraint_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "constraint_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "services", "constraint_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "constraint_service.py")),
]

# ----------------- Minimal dependency stubs before import -----------------
def ensure(name, as_pkg=False):
    if name not in sys.modules:
        m = types.ModuleType(name)
        if as_pkg:
            m.__path__ = []
        sys.modules[name] = m
    return sys.modules[name]

# bson.ObjectId stub
bson_mod = ensure("bson")
class _ObjectId:
    def __init__(self, v): self.v = str(v)
    def __repr__(self): return f"OID({self.v})"
bson_mod.ObjectId = _ObjectId

# schemas.entities stubs
schemas_pkg = ensure("schemas", as_pkg=True)
schemas_entities = ensure("schemas.entities")
class ConstraintType:
    AVOID_TOLLS = "AVOID_TOLLS"
    AVOID_HIGHWAYS = "AVOID_HIGHWAYS"
    AVOID_FERRIES = "AVOID_FERRIES"
    SHORTEST_ROUTE = "SHORTEST_ROUTE"
    FASTEST_ROUTE = "FASTEST_ROUTE"
    FUEL_EFFICIENT = "FUEL_EFFICIENT"
    AVOID_AREA = "AVOID_AREA"
    PREFERRED_ROUTE = "PREFERRED_ROUTE"
schemas_entities.ConstraintType = ConstraintType

class TripConstraint:
    def __init__(self, **data):
        self.__dict__.update(data)
        # normalize id fields
        if "_id" in data and "id" not in data:
            self.id = str(data["_id"])
    def dict(self):
        d = dict(self.__dict__)
        # keep id present
        if "_id" not in d and "id" in d:
            d["_id"] = d["id"]
        return d
schemas_entities.TripConstraint = TripConstraint

# schemas.requests stubs
schemas_requests = ensure("schemas.requests")
class CreateConstraintRequest:
    def __init__(self, **data):
        self._data = dict(data)
        for k, v in data.items(): setattr(self, k, v)
    def dict(self): return dict(self._data)
schemas_requests.CreateConstraintRequest = CreateConstraintRequest

class UpdateConstraintRequest:
    def __init__(self, **data):
        self._data = dict(data)
        for k, v in data.items(): setattr(self, k, v)
    def dict(self, exclude_unset=False):
        # treat keys with value None as unset if exclude_unset=True
        if not exclude_unset: return dict(self._data)
        return {k: v for k, v in self._data.items() if v is not None}
schemas_requests.UpdateConstraintRequest = UpdateConstraintRequest

# repositories.database.db_manager stub
repositories_pkg = ensure("repositories", as_pkg=True)
repositories_database = ensure("repositories.database")

class _InsertResult:
    def __init__(self, inserted_id): self.inserted_id = inserted_id

class _UpdateResult:
    def __init__(self, modified_count): self.modified_count = modified_count

class _DeleteResult:
    def __init__(self, deleted_count): self.deleted_count = deleted_count

class _AsyncCursor:
    def __init__(self, docs):
        self._docs = list(docs)
    def sort(self, key, direction):
        reverse = direction == -1
        self._docs.sort(key=lambda x: x.get(key), reverse=reverse)
        return self
    def __aiter__(self):
        self._i = 0
        return self
    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        d = self._docs[self._i]; self._i += 1
        return d

class _TripsCollection:
    def __init__(self):
        self.docs = {}  # key: trip_id(str) -> trip doc
        self.updates = []  # record update_one calls
    async def find_one(self, filt):
        _id = filt.get("_id")
        key = getattr(_id, "v", _id)  # our OID stub stores .v
        return self.docs.get(str(key))
    async def update_one(self, filt, update):
        self.updates.append((filt, update))
        key = getattr(filt.get("_id"), "v", filt.get("_id"))
        trip = self.docs.get(str(key))
        if not trip:
            return _UpdateResult(0)
        # apply $push and $set simply
        if "$push" in update:
            for k, v in update["$push"].items():
                trip.setdefault(k, []).append(v)
        if "$set" in update:
            trip.update(update["$set"])
        return _UpdateResult(1)

class _ConstraintsCollection:
    def __init__(self):
        self.docs = {}  # key: str id -> doc
        self.next = 1
        self.update_returns_zero = set()  # ids for which update returns 0
        self.delete_returns_zero = set()
    async def insert_one(self, data):
        cid = f"c{self.next}"; self.next += 1
        self.docs[cid] = {"_id": cid, **data}
        return _InsertResult(cid)
    async def find_one(self, filt):
        _id = filt.get("_id")
        key = getattr(_id, "v", _id)
        if key in self.docs:
            return dict(self.docs[key])
        return None
    def _match(self, doc, filt):
        for k, v in filt.items():
            if doc.get(k) != v:
                return False
        return True
    def find(self, filt):
        matches = [dict(d) for d in self.docs.values() if self._match(d, filt)]
        return _AsyncCursor(matches)
    async def update_one(self, filt, update):
        key = getattr(filt.get("_id"), "v", filt.get("_id"))
        if key not in self.docs:
            return _UpdateResult(0)
        if key in self.update_returns_zero:
            return _UpdateResult(0)
        if "$set" in update:
            self.docs[key].update(update["$set"])
        return _UpdateResult(1)
    async def delete_one(self, filt):
        key = getattr(filt.get("_id"), "v", filt.get("_id"))
        if key in self.delete_returns_zero:
            return _DeleteResult(0)
        if key in self.docs:
            del self.docs[key]
            return _DeleteResult(1)
        return _DeleteResult(0)

class _DBManager:
    def __init__(self):
        self.trips = _TripsCollection()
        self.trip_constraints = _ConstraintsCollection()

repositories_database.db_manager = _DBManager()

# ----------------- Load the service module by path -----------------
def _load_module():
    for p in CANDIDATES:
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("services.constraint_service", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.constraint_service"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("constraint_service.py not found")

cs_mod = _load_module()
ConstraintService = cs_mod.ConstraintService
ConstraintType = schemas_entities.ConstraintType
CreateConstraintRequest = schemas_requests.CreateConstraintRequest
UpdateConstraintRequest = schemas_requests.UpdateConstraintRequest

def make_service():
    return ConstraintService()

# ----------------- Tests -----------------
@pytest.mark.asyncio
async def test_add_constraint_trip_not_found_raises():
    svc = make_service()
    req = CreateConstraintRequest(type=ConstraintType.AVOID_TOLLS, value=None, priority=3)
    with pytest.raises(ValueError):
        await svc.add_constraint_to_trip("T999", req)

@pytest.mark.asyncio
async def test_add_constraint_validation_errors_avoid_area_and_preferred_route():
    svc = make_service()
    # set up trip
    db = repositories_database.db_manager
    db.trips.docs["T1"] = {"_id": "T1", "constraints": []}
    # AVOID_AREA missing fields
    bad1 = CreateConstraintRequest(type=ConstraintType.AVOID_AREA, value={"radius": 1}, priority=1)
    with pytest.raises(ValueError):
        await svc.add_constraint_to_trip("T1", bad1)
    # AVOID_AREA bad center
    bad2 = CreateConstraintRequest(type=ConstraintType.AVOID_AREA, value={"center": {"x": 1}, "radius": 1}, priority=1)
    with pytest.raises(ValueError):
        await svc.add_constraint_to_trip("T1", bad2)
    # AVOID_AREA bad radius
    bad3 = CreateConstraintRequest(type=ConstraintType.AVOID_AREA, value={"center": {"coordinates": [0,0]}, "radius": 0}, priority=1)
    with pytest.raises(ValueError):
        await svc.add_constraint_to_trip("T1", bad3)
    # PREFERRED_ROUTE requires waypoints list
    bad4 = CreateConstraintRequest(type=ConstraintType.PREFERRED_ROUTE, value={"waypoints": "not-list"}, priority=1)
    with pytest.raises(ValueError):
        await svc.add_constraint_to_trip("T1", bad4)

@pytest.mark.asyncio
async def test_add_constraint_success_inserts_and_updates_trip():
    svc = make_service()
    db = repositories_database.db_manager
    db.trips.docs["T2"] = {"_id": "T2", "constraints": []}
    req = CreateConstraintRequest(type=ConstraintType.AVOID_TOLLS, value=None, priority=5)
    out = await svc.add_constraint_to_trip("T2", req)
    assert isinstance(out, TripConstraint)
    assert out.trip_id == "T2" and out.type == ConstraintType.AVOID_TOLLS and out.is_active is True
    # trip updated with push and set
    assert db.trips.updates, "trip update_one not called"

@pytest.mark.asyncio
async def test_get_trip_constraints_and_errors(monkeypatch):
    svc = make_service()
    db = repositories_database.db_manager
    # seed constraints
    await db.trip_constraints.insert_one({"trip_id":"TX","type":ConstraintType.AVOID_TOLLS,"value":None,"priority":1,"is_active":True,"created_at":"now"})
    await db.trip_constraints.insert_one({"trip_id":"TX","type":ConstraintType.FASTEST_ROUTE,"value":None,"priority":2,"is_active":True,"created_at":"now"})
    out = await svc.get_trip_constraints("TX")
    assert len(out) == 2 and all(isinstance(c, TripConstraint) for c in out)
    # error path
    orig_find = db.trip_constraints.find
    def boom(_): raise RuntimeError("find fail")
    db.trip_constraints.find = boom
    with pytest.raises(RuntimeError):
        await svc.get_trip_constraints("TX")
    db.trip_constraints.find = orig_find

@pytest.mark.asyncio
async def test_get_constraint_by_id_found_and_none():
    svc = make_service()
    db = repositories_database.db_manager
    ins = await db.trip_constraints.insert_one({"trip_id":"T3","type":ConstraintType.FASTEST_ROUTE,"value":None,"priority":1,"is_active":True,"created_at":"now"})
    c = await svc.get_constraint_by_id(ins.inserted_id)
    assert isinstance(c, TripConstraint) and c.trip_id == "T3"
    assert await svc.get_constraint_by_id("nope") is None

@pytest.mark.asyncio
async def test_update_constraint_not_found_none_and_invalid_value_and_nomodified():
    svc = make_service()
    # not found
    out = await svc.update_constraint("c999", UpdateConstraintRequest(priority=2))
    assert out is None
    # existing with invalid value for type
    db = repositories_database.db_manager
    ins = await db.trip_constraints.insert_one({"trip_id":"T4","type":ConstraintType.AVOID_AREA,"value":{"center":{"coordinates":[0,0]},"radius": 1},"priority":1,"is_active":True,"created_at":"now"})
    with pytest.raises(ValueError):
        await svc.update_constraint(ins.inserted_id, UpdateConstraintRequest(value={"radius": 2}))  # missing center
    # modified_count == 0 path
    db.trip_constraints.update_returns_zero.add(ins.inserted_id)
    assert await svc.update_constraint(ins.inserted_id, UpdateConstraintRequest(priority=3)) is None
    db.trip_constraints.update_returns_zero.clear()

@pytest.mark.asyncio
async def test_update_constraint_success_triggers_trip_array_refresh():
    svc = make_service()
    db = repositories_database.db_manager
    db.trips.docs["T5"] = {"_id":"T5","constraints":[]}
    ins = await db.trip_constraints.insert_one({"trip_id":"T5","type":ConstraintType.FUEL_EFFICIENT,"value":None,"priority":4,"is_active":True,"created_at":"now"})
    out = await svc.update_constraint(ins.inserted_id, UpdateConstraintRequest(priority=7))
    assert isinstance(out, TripConstraint) and out.priority == 7
    # trip.update_one was invoked by _update_trip_constraints
    assert db.trips.updates, "expected trips.update_one in _update_trip_constraints"

@pytest.mark.asyncio
async def test_remove_constraint_not_found_false_delete_zero_false_and_success_true():
    svc = make_service()
    db = repositories_database.db_manager
    # not found
    assert await svc.remove_constraint("nope") is False
    # present but delete returns 0
    ins = await db.trip_constraints.insert_one({"trip_id":"T6","type":ConstraintType.AVOID_HIGHWAYS,"value":None,"priority":2,"is_active":True,"created_at":"now"})
    db.trip_constraints.delete_returns_zero.add(ins.inserted_id)
    assert await svc.remove_constraint(ins.inserted_id) is False
    db.trip_constraints.delete_returns_zero.clear()
    # success
    db.trips.docs["T6"] = {"_id":"T6","constraints":[]}
    ins2 = await db.trip_constraints.insert_one({"trip_id":"T6","type":ConstraintType.AVOID_HIGHWAYS,"value":None,"priority":2,"is_active":True,"created_at":"now"})
    assert await svc.remove_constraint(ins2.inserted_id) is True
    assert db.trips.updates, "expected trips.update_one after delete"

@pytest.mark.asyncio
async def test_get_active_constraints_for_trip_sorted_descending():
    svc = make_service()
    db = repositories_database.db_manager
    # create mixed active/inactive
    await db.trip_constraints.insert_one({"trip_id":"TA","type":ConstraintType.AVOID_TOLLS,"value":None,"priority":3,"is_active":True,"created_at":"now"})
    await db.trip_constraints.insert_one({"trip_id":"TA","type":ConstraintType.FASTEST_ROUTE,"value":None,"priority":7,"is_active":True,"created_at":"now"})
    await db.trip_constraints.insert_one({"trip_id":"TA","type":ConstraintType.AVOID_FERRIES,"value":None,"priority":1,"is_active":False,"created_at":"now"})
    out = await svc.get_active_constraints_for_trip("TA")
    assert [c.priority for c in out] == sorted([c.priority for c in out], reverse=True)
    assert all(c.is_active for c in out)

@pytest.mark.asyncio
async def test_apply_constraints_to_route_all_flags_and_lists(monkeypatch):
    svc = make_service()
    # craft constraints in desired order
    constraints = [
        TripConstraint(_id="x1", trip_id="T7", type=ConstraintType.AVOID_TOLLS, value=None, priority=1, is_active=True),
        TripConstraint(_id="x2", trip_id="T7", type=ConstraintType.AVOID_HIGHWAYS, value=None, priority=2, is_active=True),
        TripConstraint(_id="x3", trip_id="T7", type=ConstraintType.AVOID_FERRIES, value=None, priority=3, is_active=True),
        TripConstraint(_id="x4", trip_id="T7", type=ConstraintType.SHORTEST_ROUTE, value=None, priority=4, is_active=True),
        TripConstraint(_id="x5", trip_id="T7", type=ConstraintType.FASTEST_ROUTE, value=None, priority=5, is_active=True),
        TripConstraint(_id="x6", trip_id="T7", type=ConstraintType.FUEL_EFFICIENT, value=None, priority=6, is_active=True),
        TripConstraint(_id="x7", trip_id="T7", type=ConstraintType.AVOID_AREA, value={"center":{"coordinates":[1,2]},"radius":5}, priority=7, is_active=True),
        TripConstraint(_id="x8", trip_id="T7", type=ConstraintType.PREFERRED_ROUTE, value={"waypoints":[{"lat":1,"lng":2},{"lat":3,"lng":4}]}, priority=8, is_active=True),
    ]
    async def fake_get_active(trip_id): return constraints
    monkeypatch.setattr(svc, "get_active_constraints_for_trip", fake_get_active)
    out = await svc.apply_constraints_to_route("T7", {"base":"ok"})
    assert out["avoid_tolls"] is True
    assert out["avoid_highways"] is True
    assert out["avoid_ferries"] is True
    assert out["optimization"] == "fuel"  # last optimization wins
    assert out["avoid_areas"] == [constraints[6].value]
    assert out["preferred_waypoints"] == constraints[7].value["waypoints"]

@pytest.mark.asyncio
async def test_update_trip_constraints_swallow_errors(monkeypatch):
    svc = make_service()
    async def boom(*a, **k): raise RuntimeError("x")
    monkeypatch.setattr(svc, "get_trip_constraints", boom)
    # should not raise
    await svc._update_trip_constraints("T8")


@pytest.mark.asyncio
async def test_get_constraint_templates_contains_known_types():
    svc = make_service()
    templates = await svc.get_constraint_templates()
    assert len(templates) == 6
    types = {t["type"] for t in templates}
    assert ConstraintType.AVOID_TOLLS in types
    assert ConstraintType.FASTEST_ROUTE in types
