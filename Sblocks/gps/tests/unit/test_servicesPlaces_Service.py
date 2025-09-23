import sys
import types
import importlib
import importlib.util
from pathlib import Path
import pytest
from datetime import datetime

SERVICE_IMPORT_CANDIDATES = [
    "gps.services.places_service",
    "services.places_service",
    "places_service",
]

def _compute_fallback_service_path():
    here = Path(__file__).resolve()
    for i in range(0, min(10, len(here.parents))):
        base = here.parents[i]
        for p in (
            base / "services" / "places_service.py",
            base / "gps" / "services" / "places_service.py",
        ):
            if p.exists():
                return str(p)
    return None

FALLBACK_SERVICE_PATH = _compute_fallback_service_path()

class FakeInsertResult:
    def __init__(self, inserted_id="fake_oid"):
        self.inserted_id = inserted_id

class FakeUpdateResult:
    def __init__(self, modified_count=1):
        self.modified_count = modified_count

class FakeDeleteResult:
    def __init__(self, deleted_count=1):
        self.deleted_count = deleted_count

class FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self.sort_args = None
        self.skip_n = 0
        self.limit_n = None
    def sort(self, key, direction):
        self.sort_args = (key, direction)
        try:
            self._docs.sort(key=lambda d: d.get(key), reverse=(direction == -1))
        except Exception:
            pass
        return self
    def skip(self, n):
        self.skip_n = n
        self._docs = self._docs[n:]
        return self
    def limit(self, n):
        self.limit_n = n
        if n is not None:
            self._docs = self._docs[:n]
        return self
    def __aiter__(self):
        async def gen():
            for d in self._docs:
                yield d
        return gen()

class FakeAggregateCursor:
    def __init__(self, docs):
        self._docs = list(docs)
    def __aiter__(self):
        async def gen():
            for d in self._docs:
                yield d
        return gen()

class FakePlacesCollection:
    def __init__(self):
        self.last_find_query = None
        self.last_update_filter = None
        self.last_update_doc = None
        self.last_delete_filter = None
        self.last_insert_doc = None
        self.last_aggregate_pipeline = None
        self.find_docs = []
        self.find_one_doc = None
        self.find_raises = False
        self.find_one_raises = False
        self.aggregate_docs = []
        self.aggregate_raises = False
        self.update_one_result = FakeUpdateResult(1)
        self.delete_one_result = FakeDeleteResult(1)
        self.insert_result = FakeInsertResult("oid123")
    async def insert_one(self, doc):
        self.last_insert_doc = doc
        return self.insert_result
    def find(self, query):
        if self.find_raises:
            raise RuntimeError("find error")
        self.last_find_query = query
        return FakeCursor(self.find_docs)
    async def find_one(self, flt):
        if self.find_one_raises:
            raise RuntimeError("find_one error")
        self.last_find_query = flt
        return self.find_one_doc
    async def update_one(self, flt, update):
        self.last_update_filter = flt
        self.last_update_doc = update
        return self.update_one_result
    async def delete_one(self, flt):
        self.last_delete_filter = flt
        return self.delete_one_result
    def aggregate(self, pipeline):
        if self.aggregate_raises:
            raise RuntimeError("aggregate error")
        self.last_aggregate_pipeline = pipeline
        return FakeAggregateCursor(self.aggregate_docs)

class FakeDB:
    def __init__(self):
        self.places = FakePlacesCollection()

class FakeDBManager:
    def __init__(self):
        self.db = FakeDB()

def make_fake_entities_module():
    m = types.ModuleType("schemas.entities")
    class Place:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    m.Place = Place
    return m

def make_fake_events_module(raise_on_publish=False, calls_sink=None):
    pub = types.ModuleType("events.publisher")
    calls = calls_sink if calls_sink is not None else []
    class _Publisher:
        def __init__(self):
            self.calls = calls
        async def publish_place_created(self, **kwargs):
            if raise_on_publish:
                raise RuntimeError("publish fail")
            self.calls.append(("place_created", kwargs))
    pub.event_publisher = _Publisher()
    return pub

def make_fake_bson_module(store=None):
    m = types.ModuleType("bson")
    class ObjectId:
        def __init__(self, s):
            if store is not None:
                store["last_oid"] = s
            self._s = s
        def __str__(self):
            return self._s
        @staticmethod
        def is_valid(s: str) -> bool:
            return isinstance(s, str) and len(s) == 24
    m.ObjectId = ObjectId
    return m

class SysModulesSandbox:
    def __init__(self, *, publish_raises=False, publisher_calls=None, bson_store=None):
        self.publish_raises = publish_raises
        self.publisher_calls = publisher_calls if publisher_calls is not None else []
        self.bson_store = bson_store if bson_store is not None else {}
        self._orig = None
        self.db_manager = None
    def __enter__(self):
        self._orig = sys.modules.copy()
        repositories_pkg = types.ModuleType("repositories")
        database_mod = types.ModuleType("repositories.database")
        self.db_manager = FakeDBManager()
        database_mod.db_manager = self.db_manager
        schemas_pkg = types.ModuleType("schemas")
        entities_mod = make_fake_entities_module()
        events_pkg = types.ModuleType("events")
        publisher_mod = make_fake_events_module(
            raise_on_publish=self.publish_raises,
            calls_sink=self.publisher_calls
        )
        bson_mod = make_fake_bson_module(store=self.bson_store)
        sys.modules["repositories"] = repositories_pkg
        sys.modules["repositories.database"] = database_mod
        sys.modules["schemas"] = schemas_pkg
        sys.modules["schemas.entities"] = entities_mod
        sys.modules["events"] = events_pkg
        sys.modules["events.publisher"] = publisher_mod
        sys.modules["bson"] = bson_mod
        return self
    def __exit__(self, exc_type, exc, tb):
        sys.modules.clear()
        sys.modules.update(self._orig)

def import_service_module():
    last_err = None
    for name in SERVICE_IMPORT_CANDIDATES:
        try:
            if name in sys.modules:
                del sys.modules[name]
            return importlib.import_module(name)
        except Exception as e:
            last_err = e
    if FALLBACK_SERVICE_PATH:
        spec = importlib.util.spec_from_file_location("places_service", FALLBACK_SERVICE_PATH)
        mod = importlib.util.module_from_spec(spec)
        if "places_service" in sys.modules:
            del sys.modules["places_service"]
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    raise last_err or ImportError("Unable to import places_service")

#------------create_place happy--------
@pytest.mark.asyncio
async def test_create_place_happy():
    calls = []
    with SysModulesSandbox(publisher_calls=calls) as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.insert_result = FakeInsertResult("cafebabe")
        place = await svc.create_place(
            user_id="u1", name="Home", description="desc", latitude=1.5, longitude=2.5
        )
        ins = sb.db_manager.db.places.last_insert_doc
        assert ins["location"]["type"] == "Point"
        assert ins["location"]["coordinates"] == [2.5, 1.5]
        assert place._id == "cafebabe"
        assert calls and calls[0][0] == "place_created"

#------------create_place publisher error swallowed--------
@pytest.mark.asyncio
async def test_create_place_publisher_error_swallowed():
    with SysModulesSandbox(publish_raises=True) as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        res = await svc.create_place(user_id="u2", name="X", description=None, latitude=0, longitude=0)
        assert isinstance(res, object)

#------------create_place insert raises--------
@pytest.mark.asyncio
async def test_create_place_insert_raises():
    class Boom(FakePlacesCollection):
        async def insert_one(self, doc):
            raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.places = Boom()
        mod = import_service_module()
        svc = mod.PlacesService()
        with pytest.raises(RuntimeError):
            await svc.create_place("u", "n", None, 0, 0)

#------------get_place found--------
@pytest.mark.asyncio
async def test_get_place_found():
    store = {}
    with SysModulesSandbox(bson_store=store) as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_one_doc = {"_id": "ABC", "user_id":"u", "name":"N"}
        res = await svc.get_place("1"*24)
        assert res._id == "ABC"
        assert store["last_oid"] == "1"*24

#------------get_place not found--------
@pytest.mark.asyncio
async def test_get_place_not_found():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_one_doc = None
        res = await svc.get_place("1"*24)
        assert res is None

#------------get_place db error--------
@pytest.mark.asyncio
async def test_get_place_db_error():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_one_raises = True
        with pytest.raises(RuntimeError):
            await svc.get_place("1"*24)

#------------get_place_by_id invalid id--------
@pytest.mark.asyncio
async def test_get_place_by_id_invalid_returns_none():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        res = await svc.get_place_by_id("short")
        assert res is None

#------------get_place_by_id valid found--------
@pytest.mark.asyncio
async def test_get_place_by_id_valid_found():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_one_doc = {"_id": "XYZ", "user_id":"u", "name":"N"}
        res = await svc.get_place_by_id("1"*24)
        assert res._id == "XYZ"

#------------get_place_by_id valid not found--------
@pytest.mark.asyncio
async def test_get_place_by_id_valid_not_found():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_one_doc = None
        res = await svc.get_place_by_id("1"*24)
        assert res is None

#------------get_place_by_id db error returns none--------
@pytest.mark.asyncio
async def test_get_place_by_id_db_error_returns_none():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_one_raises = True
        res = await svc.get_place_by_id("1"*24)
        assert res is None

#------------get_places with filter--------
@pytest.mark.asyncio
async def test_get_places_with_filter_and_pagination():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_docs = [{"_id":"A","name":"a"},{"_id":"B","name":"b"}]
        res = await svc.get_places(place_type="home", skip=0, limit=2)
        assert [r._id for r in res] == ["A","B"]
        assert sb.db_manager.db.places.last_find_query == {"place_type":"home"}

#------------get_places db error--------
@pytest.mark.asyncio
async def test_get_places_db_error():
    class Boom(FakePlacesCollection):
        def find(self, q):
            raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.places = Boom()
        mod = import_service_module()
        svc = mod.PlacesService()
        with pytest.raises(RuntimeError):
            await svc.get_places()

#------------get_user_places with filters--------
@pytest.mark.asyncio
async def test_get_user_places_with_filters():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_docs = [{"_id":"1"},{"_id":"2"}]
        res = await svc.get_user_places(user_id="u1", place_type="work", limit=2, offset=0)
        assert len(res) == 2
        assert sb.db_manager.db.places.last_find_query == {"user_id":"u1","place_type":"work"}

#------------get_user_places db error--------
@pytest.mark.asyncio
async def test_get_user_places_db_error():
    class Boom(FakePlacesCollection):
        def find(self, q):
            raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.places = Boom()
        mod = import_service_module()
        svc = mod.PlacesService()
        with pytest.raises(RuntimeError):
            await svc.get_user_places("u")

#------------search_places query shape--------
@pytest.mark.asyncio
async def test_search_places_query_shape_and_result():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_docs = [{"_id":"S"}]
        res = await svc.search_places("u1","Park",limit=10)
        q = sb.db_manager.db.places.last_find_query
        assert q["user_id"] == "u1"
        ors = q["$or"]
        assert ors[0]["name"]["$regex"] == "Park" and ors[0]["name"]["$options"] == "i"
        assert ors[1]["description"]["$regex"] == "Park" and ors[1]["description"]["$options"] == "i"
        assert ors[2]["address"]["$regex"] == "Park" and ors[2]["address"]["$options"] == "i"
        assert [r._id for r in res] == ["S"]

#------------search_places db error--------
@pytest.mark.asyncio
async def test_search_places_db_error():
    class Boom(FakePlacesCollection):
        def find(self, q):
            raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.places = Boom()
        mod = import_service_module()
        svc = mod.PlacesService()
        with pytest.raises(RuntimeError):
            await svc.search_places("u","x")

#------------get_places_near_location happy--------
@pytest.mark.asyncio
async def test_get_places_near_location_happy():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.find_docs = [{"_id":"N1"}]
        res = await svc.get_places_near_location("u1", 10.0, 20.0, radius_meters=1500, limit=5)
        q = sb.db_manager.db.places.last_find_query
        geo = q["location"]["$near"]["$geometry"]
        assert q["user_id"] == "u1"
        assert geo["type"] == "Point" and geo["coordinates"] == [20.0, 10.0]
        assert q["location"]["$near"]["$maxDistance"] == 1500
        assert [r._id for r in res] == ["N1"]

#------------get_places_near_location db error--------
@pytest.mark.asyncio
async def test_get_places_near_location_db_error():
    class Boom(FakePlacesCollection):
        def find(self, q):
            raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.places = Boom()
        mod = import_service_module()
        svc = mod.PlacesService()
        with pytest.raises(RuntimeError):
            await svc.get_places_near_location("u",0,0)

#------------update_place only name, modified returns model--------
@pytest.mark.asyncio
async def test_update_place_only_name_returns_model():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.update_one_result = FakeUpdateResult(1)
        sb.db_manager.db.places.find_one_doc = {"_id":"RID","name":"NewName"}
        res = await svc.update_place(place_id="1"*24, user_id="u1", name="NewName")
        setdoc = sb.db_manager.db.places.last_update_doc["$set"]
        assert "name" in setdoc and "location" not in setdoc
        assert res._id == "RID"

#------------update_place lat_lng updates location--------
@pytest.mark.asyncio
async def test_update_place_with_lat_lng_updates_location():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.update_one_result = FakeUpdateResult(1)
        sb.db_manager.db.places.find_one_doc = {"_id":"RID2","latitude":9.0,"longitude":8.0}
        res = await svc.update_place(place_id="1"*24, user_id="u2", latitude=9.0, longitude=8.0)
        setdoc = sb.db_manager.db.places.last_update_doc["$set"]
        assert setdoc["location"]["coordinates"] == [8.0, 9.0]
        assert res._id == "RID2"

#------------update_place modified_count_zero_returns_none--------
@pytest.mark.asyncio
async def test_update_place_modified_zero_returns_none():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.update_one_result = FakeUpdateResult(0)
        res = await svc.update_place(place_id="1"*24, user_id="u3", name="N")
        assert res is None

#------------update_place db error--------
@pytest.mark.asyncio
async def test_update_place_db_error():
    class Boom(FakePlacesCollection):
        async def update_one(self, flt, upd):
            raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.places = Boom()
        mod = import_service_module()
        svc = mod.PlacesService()
        with pytest.raises(RuntimeError):
            await svc.update_place(place_id="1"*24, user_id="u", name="x")

#------------delete_place true/false--------
@pytest.mark.asyncio
async def test_delete_place_true_and_false():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.delete_one_result = FakeDeleteResult(1)
        ok = await svc.delete_place("1"*24, "u1")
        assert ok is True
        sb.db_manager.db.places.delete_one_result = FakeDeleteResult(0)
        ok2 = await svc.delete_place("1"*24, "u1")
        assert ok2 is False

#------------delete_place db error--------
@pytest.mark.asyncio
async def test_delete_place_db_error():
    class Boom(FakePlacesCollection):
        async def delete_one(self, flt):
            raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.places = Boom()
        mod = import_service_module()
        svc = mod.PlacesService()
        with pytest.raises(RuntimeError):
            await svc.delete_place("1"*24, "u")

#------------get_place_statistics counts--------
@pytest.mark.asyncio
async def test_get_place_statistics_counts():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.aggregate_docs = [{"_id":"home","count":2},{"_id":"work","count":1}]
        stats = await svc.get_place_statistics("u1")
        assert stats["user_id"] == "u1"
        assert stats["total_places"] == 3
        assert stats["place_counts_by_type"] == {"home":2,"work":1}

#------------get_place_statistics empty--------
@pytest.mark.asyncio
async def test_get_place_statistics_empty():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.aggregate_docs = []
        stats = await svc.get_place_statistics("u2")
        assert stats["total_places"] == 0
        assert stats["place_counts_by_type"] == {}

#------------get_place_statistics db error--------
@pytest.mark.asyncio
async def test_get_place_statistics_db_error():
    class Boom(FakePlacesCollection):
        def aggregate(self, pipeline):
            raise RuntimeError("boom")
    with SysModulesSandbox() as sb:
        sb.db_manager.db.places = Boom()
        mod = import_service_module()
        svc = mod.PlacesService()
        with pytest.raises(RuntimeError):
            await svc.get_place_statistics("u")

#------------update_place sets description/address/type/metadata--------
@pytest.mark.asyncio
async def test_update_place_sets_description_address_type_metadata():
    with SysModulesSandbox() as sb:
        mod = import_service_module()
        svc = mod.PlacesService()
        sb.db_manager.db.places.update_one_result = FakeUpdateResult(1)
        sb.db_manager.db.places.find_one_doc = {
            "_id": "RID3",
            "description": "D",
            "address": "Addr",
            "place_type": "home",
            "metadata": {"k": "v"},
        }
        res = await svc.update_place(
            place_id="1"*24,
            user_id="u1",
            description="D",
            address="Addr",
            place_type="home",
            metadata={"k": "v"},
        )
        setdoc = sb.db_manager.db.places.last_update_doc["$set"]
        assert setdoc["description"] == "D"
        assert setdoc["address"] == "Addr"
        assert setdoc["place_type"] == "home"
        assert setdoc["metadata"] == {"k": "v"}
        assert "location" not in setdoc
        assert res._id == "RID3"

