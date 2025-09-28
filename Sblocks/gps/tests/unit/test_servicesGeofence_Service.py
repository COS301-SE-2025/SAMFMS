import sys
import types
import importlib
import importlib.util
from pathlib import Path
import pytest

SERVICE_IMPORT_CANDIDATES = [

    "gps.services.geofence_service",

    "trip_planning.services.geofence_service",

    "services.geofence_service",
    "geofence_service",
]

def _compute_fallback_service_path() -> str | None:
    here = Path(__file__).resolve()
    print(f"[DEBUG] _compute_fallback_service_path starting from: {here}")
    here = Path(__file__).resolve()
    for i in range(0, min(8, len(here.parents))):
        base = here.parents[i]
        candidates = [
            base / "services" / "geofence_service.py",
            base / "gps" / "services" / "geofence_service.py",
        ]
        for c in candidates:
            if c.exists():
                print(f"[DEBUG] Found fallback service path: {c}")
                return str(c)
    print("[DEBUG] No fallback service path found")
    return None

FALLBACK_SERVICE_PATH = _compute_fallback_service_path()

class FakeInsertResult:
    def __init__(self, inserted_id="fake_insert_id"):
        self.inserted_id = inserted_id

class FakeUpdateResult:
    def __init__(self, modified_count=1):
        self.modified_count = modified_count

class FakeDeleteResult:
    def __init__(self, deleted_count=1):
        self.deleted_count = deleted_count

class FakeCursor:
    def __init__(self, docs):
        self._docs = docs
        self.params = {"skip": 0, "limit": None}

    def skip(self, n):
        self.params["skip"] = n
        return self

    def limit(self, n):
        self.params["limit"] = n
        return self

    def __aiter__(self):
        async def gen():
            for d in self._docs:
                yield d
        return gen()

class FakeCollection:
    def __init__(self):
        self.last_insert_data = None
        self.last_update_filter = None
        self.last_update_data = None
        self.last_find_query = None
        self.last_find_one_filter = None
        self.last_delete_filter = None
        self._find_docs = []
        self._find_raises = False
        self._find_one_doc = None
        self._find_one_raises = False
        self._update_result = FakeUpdateResult(1)
        self._delete_result = FakeDeleteResult(1)
        self._insert_result = FakeInsertResult("fake_oid")

    def set_find_docs(self, docs):
        self._find_docs = docs

    def set_find_raises(self, raises=True):
        self._find_raises = raises

    def set_find_one_doc(self, doc):
        self._find_one_doc = doc

    def set_find_one_raises(self, raises=True):
        self._find_one_raises = raises

    def set_update_result(self, modified_count):
        self._update_result = FakeUpdateResult(modified_count)

    def set_delete_result(self, deleted_count):
        self._delete_result = FakeDeleteResult(deleted_count)

    def set_insert_id(self, oid):
        self._insert_result = FakeInsertResult(oid)

    async def insert_one(self, data):
        self.last_insert_data = data
        return self._insert_result

    def find(self, query):
        if self._find_raises:
            raise RuntimeError("find error")
        self.last_find_query = query
        return FakeCursor(list(self._find_docs))

    async def find_one(self, flt):
        if self._find_one_raises:
            raise RuntimeError("find_one error")
        self.last_find_one_filter = flt
        return self._find_one_doc

    async def update_one(self, flt, update):
        self.last_update_filter = flt
        self.last_update_data = update
        return self._update_result

    async def delete_one(self, flt):
        self.last_delete_filter = flt
        return self._delete_result

class FakeDB:
    def __init__(self, name="fake_db"):
        self.name = name
        self.geofences = FakeCollection()

class FakeDBManager:
    def __init__(self):
        self.db = FakeDB()

def make_fake_entities_module():
    entities = types.ModuleType("schemas.entities")

    class Geofence:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class GeofenceCenter:
        def __init__(self, latitude: float, longitude: float):
            self.latitude = latitude
            self.longitude = longitude

    class GeofenceGeometry:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

            self.type = kwargs.get("type")

            center = kwargs.get("center")
            if isinstance(center, dict):
                self.center = GeofenceCenter(
                    latitude=center.get("latitude"),
                    longitude=center.get("longitude"),
                )
            else:
                self.center = center

            self.radius = kwargs.get("radius")
            self.points = kwargs.get("points")

    class GeofenceType:
        CIRCLE = "circle"
        POLYGON = "polygon"
        RECTANGLE = "rectangle"

    def GeofenceCategory(val):
        return str(val).lower()

    def GeofenceStatus(val):
        return str(val).lower()

    entities.Geofence = Geofence
    entities.GeofenceGeometry = GeofenceGeometry
    entities.GeofenceCenter = GeofenceCenter
    entities.GeofenceType = GeofenceType
    entities.GeofenceStatus = GeofenceStatus
    entities.GeofenceCategory = GeofenceCategory
    return entities

def make_fake_events_module(raise_on_publish=False, calls_sink=None):
    pub = types.ModuleType("events.publisher")

    _calls = calls_sink if calls_sink is not None else []

    class _EventPublisher:
        def __init__(self):
            self.calls = _calls

        async def publish_geofence_created(self, geofence_id: str, name: str):
            if raise_on_publish:
                raise RuntimeError("publish failed")
            self.calls.append({"geofence_id": geofence_id, "name": name})
    _publisher = _EventPublisher()
    pub.event_publisher = _publisher
    async def publish_geofence_created(geofence_id: str, name: str):
        await _publisher.publish_geofence_created(geofence_id, name)

    pub.publish_geofence_created = publish_geofence_created
    return pub

def make_fake_bson_module(record_last=False, store=None):
    bson_mod = types.ModuleType("bson")

    class ObjectId:
        def __init__(self, s):
            if store is not None and record_last:
                store["last_oid"] = s
            self._s = s
        def __str__(self):
            return self._s
        def __repr__(self):
            return f"FakeObjectId({self._s!r})"

    bson_mod.ObjectId = ObjectId
    return bson_mod

class SysModulesSandbox:
    def __init__(self, *, raise_on_publish=False, publisher_calls=None, bson_store=None):
        self.raise_on_publish = raise_on_publish
        self.publisher_calls = publisher_calls if publisher_calls is not None else []
        self.bson_store = bson_store if bson_store is not None else {}
        self._original = None

    def __enter__(self):
        self._original = sys.modules.copy()

        repositories_pkg = types.ModuleType("repositories")
        database_mod = types.ModuleType("repositories.database")
        database_mod.db_manager = FakeDBManager()

        schemas_pkg = types.ModuleType("schemas")
        entities_mod = make_fake_entities_module()

        events_pkg = types.ModuleType("events")
        publisher_mod = make_fake_events_module(
            raise_on_publish=self.raise_on_publish,
            calls_sink=self.publisher_calls
        )

        bson_mod = make_fake_bson_module(record_last=True, store=self.bson_store)

        sys.modules["repositories"] = repositories_pkg
        sys.modules["repositories.database"] = database_mod

        sys.modules["schemas"] = schemas_pkg
        sys.modules["schemas.entities"] = entities_mod

        sys.modules["events"] = events_pkg
        sys.modules["events.publisher"] = publisher_mod

        sys.modules["bson"] = bson_mod

        return database_mod.db_manager 

    def __exit__(self, exc_type, exc, tb):
        sys.modules.clear()
        sys.modules.update(self._original)

def import_service_module():
    last_err = None
    for name in SERVICE_IMPORT_CANDIDATES:
        print(f"[DEBUG] Attempting import: {name}")
        try:
            if name in sys.modules:
                del sys.modules[name]
            mod = importlib.import_module(name)
            print(f"[DEBUG] Imported module: {name}")
            return mod
        except Exception as e:
            print(f"[DEBUG] Import failed for {name}: {e}")
            last_err = e

    if FALLBACK_SERVICE_PATH:
        print(f"[DEBUG] Using FALLBACK_SERVICE_PATH: {FALLBACK_SERVICE_PATH}")
        spec = importlib.util.spec_from_file_location("geofence_service", FALLBACK_SERVICE_PATH)
        mod = importlib.util.module_from_spec(spec)
        if "geofence_service" in sys.modules:
            del sys.modules["geofence_service"]
        spec.loader.exec_module(mod)
        print("[DEBUG] Imported geofence_service from fallback path")  
        return mod

    raise last_err or ImportError("Unable to import geofence_service")


# -----------------------------
# -----------------------------

@pytest.mark.asyncio
async def test_create_geofence_missing_name_raises_value_error():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        with pytest.raises(ValueError):
            await svc.create_geofence(name="", geometry={"type": "circle", "center": {"latitude": 1, "longitude": 2}, "radius": 10})

@pytest.mark.asyncio
async def test_create_geofence_missing_or_invalid_geometry_raises_value_error():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        with pytest.raises(ValueError):
            await svc.create_geofence(name="A", geometry=None)
        with pytest.raises(ValueError):
            await svc.create_geofence(name="A", geometry=["not a dict"])

@pytest.mark.asyncio
async def test_create_geofence_circle_inserts_point_and_publishes():
    publisher_calls = []
    with SysModulesSandbox(publisher_calls=publisher_calls) as dbm:
        dbm.db.geofences.set_insert_id("cafebabecafebabecafebabe")
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()

        model = await svc.create_geofence(
            name="Depot 1",
            geometry={"type": "point", "coordinates": [20.25, 10.5], "radius": 150}
        )

        inserted = dbm.db.geofences.last_insert_data
        assert inserted["geometry"]["type"] == "Point"
        assert inserted["geometry"]["coordinates"] == [20.25, 10.5]
        geom = inserted["geometry"]
        radius = geom.get("radius") or (geom.get("properties") or {}).get("radius")
        assert radius == 150

        returned_id = getattr(model, "id", None) or getattr(model, "_id", None)
        assert returned_id == "cafebabecafebabecafebabe"

        assert publisher_calls and publisher_calls[0]["geofence_id"] == "cafebabecafebabecafebabe"
        assert publisher_calls[0]["name"] == "Depot 1"


@pytest.mark.asyncio
async def test_create_geofence_polygon_requires_three_points():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        with pytest.raises(ValueError):
            await svc.create_geofence(
                name="Bad poly",
                geometry={"type": "polygon", "points": [{"latitude": 1, "longitude": 2}, {"latitude": 3, "longitude": 4}]}
            )

@pytest.mark.asyncio
async def test_create_geofence_polygon_is_closed_before_insert():
    with SysModulesSandbox() as dbm:
        dbm.db.geofences.set_insert_id("xid")
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        ring = [
            [2.0, 1.0],
            [4.0, 3.0],
            [6.0, 5.0],
        ]
        await svc.create_geofence(name="P", geometry={"type": "polygon", "coordinates": [ring]})

        coords = dbm.db.geofences.last_insert_data["geometry"]["coordinates"][0]
        assert coords[0] == coords[-1] == [2.0, 1.0]


@pytest.mark.asyncio
async def test_create_geofence_unsupported_geometry_raises_value_error():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        with pytest.raises(ValueError):
            await svc.create_geofence(name="X", geometry={"type": "triangle", "points": []})

@pytest.mark.asyncio
async def test_create_geofence_publish_failure_is_swallowed():
    with SysModulesSandbox(raise_on_publish=True) as dbm:
        dbm.db.geofences.set_insert_id("ok")
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()

        model = await svc.create_geofence(
            name="Noisy",
            geometry={"type": "circle", "center": {"latitude": 0, "longitude": 0}, "radius": 1}
        )
        returned_id = getattr(model, "id", None) or getattr(model, "_id", None)
        assert returned_id == "ok"



# -----------------------------
# -----------------------------

@pytest.mark.asyncio
async def test_get_geofence_by_id_24_char_uses_objectid_and_returns_model():
    store = {}
    with SysModulesSandbox(bson_store=store) as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        dbm.db.geofences.set_find_one_doc({"_id": "OID123", "name": "A", "description": "", "type": "depot", "status": "active", "geometry": {}})
        oid = "1" * 24
        res = await svc.get_geofence_by_id(oid)
        assert store.get("last_oid") == oid
        assert res.id == "OID123"

@pytest.mark.asyncio
async def test_get_geofence_by_id_non24_raw_id_and_not_found_is_none():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        dbm.db.geofences.set_find_one_doc(None)
        res = await svc.get_geofence_by_id("short-id")
        assert res is None
        assert dbm.db.geofences.last_find_one_filter == {"_id": "short-id"}

@pytest.mark.asyncio
async def test_get_geofence_by_id_db_error_returns_none():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        dbm.db.geofences.set_find_one_raises(True)
        res = await svc.get_geofence_by_id("1" * 24)
        assert res is None


# -----------------------------
# -----------------------------

@pytest.mark.asyncio
async def test_normalize_geometry_point_to_circle():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        doc = {"geometry": {"type": "Point", "coordinates": [20.0, 10.0], "radius": 50}}
        norm = svc._normalize_geometry(doc)
        assert norm["type"] == "circle"
        assert norm["center"] == {"latitude": 10.0, "longitude": 20.0}
        assert norm["radius"] == 50

@pytest.mark.asyncio
async def test_normalize_geometry_polygon_to_polygon_points():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        doc = {"geometry": {"type": "Polygon", "coordinates": [[(20.0, 10.0), (21.0, 11.0), (20.0, 10.0)]]}}
        norm = svc._normalize_geometry(doc)
        assert norm["type"] == "polygon"
        assert norm["points"][0] == {"latitude": 10.0, "longitude": 20.0}

@pytest.mark.asyncio
async def test_normalize_geometry_unknown_passthrough():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        doc = {"geometry": {"type": "LineString", "coordinates": []}}
        assert svc._normalize_geometry(doc) == doc["geometry"]


# -----------------------------
# -----------------------------

@pytest.mark.asyncio
async def test_get_geofences_applies_filters_and_normalizes():
    with SysModulesSandbox() as dbm:
        docs = [
            {
                "_id": "1",
                "name": "C1",
                "description": "",
                "type": "depot",
                "status": "active",
                "geometry": {"type": "Point", "coordinates": [22.0, 33.0], "radius": 5},
            },
            {
                "_id": "2",
                "name": "P1",
                "description": "",
                "type": "depot",
                "status": "active",
                "geometry": {"type": "Polygon", "coordinates": [[(10.0, 1.0), (20.0, 2.0), (10.0, 1.0)]]},
            },
        ]
        dbm.db.geofences.set_find_docs(docs)
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()

        res = await svc.get_geofences(is_active=True, geofence_type="depot", limit=10, offset=5)

        assert dbm.db.geofences.last_find_query == {"is_active": True, "type": "depot"}
        assert len(res) == 2

        g0 = res[0].geometry
        assert g0["type"] == "Point"
        assert g0["coordinates"] == [22.0, 33.0]
        r0 = g0.get("radius") or (g0.get("properties") or {}).get("radius")
        assert r0 == 5

        g1 = res[1].geometry
        assert g1["type"] == "Polygon"
        assert g1["coordinates"][0][0] == (10.0, 1.0)


@pytest.mark.asyncio
async def test_get_geofences_db_error_returns_empty_list():
    with SysModulesSandbox() as dbm:
        dbm.db.geofences.set_find_raises(True)
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        res = await svc.get_geofences()
        assert res == []


# -----------------------------
# -----------------------------

@pytest.mark.asyncio
async def test_update_geofence_sets_fields_circle_geometry_and_status_active():
    with SysModulesSandbox() as dbm:
        dbm.db.geofences.set_update_result(modified_count=1)
        dbm.db.geofences.set_find_one_doc(
            {"_id": "ret", "name": "N", "description": "D", "type": "depot", "status": "active", "geometry": {}}
        )

        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()

        res = await svc.update_geofence(
            "1" * 24,
            name="New",
            description="Desc",
            geometry={"type": "circle", "center": {"latitude": 10.0, "longitude": 20.0}, "radius": 7},
            status="active",
            metadata={"a": 1},
        )

        update = dbm.db.geofences.last_update_data["$set"]
        assert update["name"] == "New"
        assert update["description"] == "Desc"

        geom = update["geometry"]
        assert geom["type"] == "Point"
        assert geom["coordinates"] == [20.0, 10.0]
        radius = geom.get("radius") or (geom.get("properties") or {}).get("radius")
        assert radius == 7

        assert update["status"] == "active"
        assert update["is_active"] is True
        assert update["metadata"] == {"a": 1}
        assert "updated_at" in update
        assert res.id == "ret"

@pytest.mark.asyncio
async def test_update_geofence_polygon_geometry_tuples_and_non24_id():
    with SysModulesSandbox() as dbm:
        dbm.db.geofences.set_update_result(1)
        dbm.db.geofences.set_find_one_doc({"_id": "X", "name": "n", "description": "", "type": "t", "status": "s", "geometry": {}})

        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()

        ring = [
            (2.0, 1.0),
            (4.0, 3.0),
            (6.0, 5.0),
        ]
        res = await svc.update_geofence(
            "short-id",
            geometry={"type": "polygon", "coordinates": [ring]},
        )

        assert dbm.db.geofences.last_update_filter == {"_id": "short-id"}
        geom = dbm.db.geofences.last_update_data["$set"]["geometry"]
        assert geom["type"] == "Polygon"
        first_pt = geom["coordinates"][0][0]
        assert tuple(first_pt) == (2.0, 1.0)
        assert res.id == "X"

@pytest.mark.asyncio
async def test_update_geofence_unsupported_geometry_returns_none():
    with SysModulesSandbox() as dbm:
        dbm.db.geofences.set_update_result(1)
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        res = await svc.update_geofence("1" * 24, geometry={"type": "triangle"})
        assert res is None

@pytest.mark.asyncio
async def test_update_geofence_modified_count_zero_returns_none():
    with SysModulesSandbox() as dbm:
        dbm.db.geofences.set_update_result(0)
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        res = await svc.update_geofence("1" * 24, name="NoChange")
        assert res is None

@pytest.mark.asyncio
async def test_update_geofence_exception_returns_none():
    class BoomCollection(FakeCollection):
        async def update_one(self, flt, update):
            raise RuntimeError("boom")

    with SysModulesSandbox() as dbm:
        dbm.db.geofences = BoomCollection()
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        res = await svc.update_geofence("1" * 24, name="X")
        assert res is None


# -----------------------------
# -----------------------------

@pytest.mark.asyncio
async def test_delete_geofence_24_char_true():
    with SysModulesSandbox() as dbm:
        dbm.db.geofences.set_delete_result(1)
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        ok = await svc.delete_geofence("1" * 24)
        assert ok is True

@pytest.mark.asyncio
async def test_delete_geofence_non24_true_and_zero_false():
    with SysModulesSandbox() as dbm:
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()

        dbm.db.geofences.set_delete_result(1)
        ok = await svc.delete_geofence("short")
        assert ok is True
        assert dbm.db.geofences.last_delete_filter == {"_id": "short"}

        dbm.db.geofences.set_delete_result(0)
        ok2 = await svc.delete_geofence("short")
        assert ok2 is False

@pytest.mark.asyncio
async def test_delete_geofence_exception_returns_false():
    class BoomCollection(FakeCollection):
        async def delete_one(self, flt):
            raise RuntimeError("boom")

    with SysModulesSandbox() as dbm:
        dbm.db.geofences = BoomCollection()
        svc_mod = import_service_module()
        svc = svc_mod.GeofenceService()
        ok = await svc.delete_geofence("x" * 24)
        assert ok is False