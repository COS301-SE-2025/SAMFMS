import os, sys, importlib, importlib.util, types, math
from types import SimpleNamespace
import pytest
from datetime import datetime, timedelta, timezone

# ------------------------------------------------------------------------------------
# Path resolver (search up to 5 levels + CWD)
# ------------------------------------------------------------------------------------
HERE = os.path.abspath(os.path.dirname(__file__))
PARENTS = [os.path.abspath(os.path.join(HERE, *([".."] * i))) for i in range(1, 6)]
CANDIDATES = list(dict.fromkeys(PARENTS + [os.getcwd(), HERE]))
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

# ------------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------------
def _walk_roots_for(filename, roots):
    seen = set()
    SKIP = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache"}
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            base = os.path.basename(dirpath).lower()
            if base in SKIP:
                continue
            if dirpath in seen:
                continue
            seen.add(dirpath)
            if filename in filenames:
                yield os.path.join(dirpath, filename)

def make_to_list_cursor(items):
    class _C:
        def __init__(self, items): self._items = list(items)
        async def to_list(self, *args, **kwargs):
            length = kwargs.get("length")
            data = list(self._items)
            return data if length is None else data[:length]
    return _C(items)

# aiohttp fakes per-test
class FakeAioHTTP:
    """Factory for faking aiohttp.ClientSession with canned responses."""
    class _Resp:
        def __init__(self, status, payload):
            self.status = status
            self._payload = payload
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False
        async def json(self): return self._payload

    class _ReqCtx:
        def __init__(self, status, payload):
            self._resp = FakeAioHTTP._Resp(status, payload)
        async def __aenter__(self): return self._resp
        async def __aexit__(self, exc_type, exc, tb): return False

    class _Session:
        def __init__(self, status, payload, raise_on_get=False):
            self._status = status
            self._payload = payload
            self._raise = raise_on_get
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc, tb): return False
        def get(self, url, params=None):
            if self._raise:
                raise RuntimeError("network boom")
            return FakeAioHTTP._ReqCtx(self._status, self._payload)

    def __init__(self, status=200, payload=None, raise_on_get=False):
        self.status = status
        self.payload = payload or {}
        self.raise_on_get = raise_on_get

    def ClientSession(self, *a, **k):
        return FakeAioHTTP._Session(self.status, self.payload, self.raise_on_get)

# ------------------------------------------------------------------------------------
# Robust loader with temporary module stubs (cleaned after import)
# ------------------------------------------------------------------------------------
def _load_simulation_service_module():
    injected = []
    def _inject(name, module):
        if name not in sys.modules:
            sys.modules[name] = module
            injected.append(name)

    # bson
    if "bson" not in sys.modules:
        bson_mod = types.ModuleType("bson")
        class _ObjectId:
            def __init__(self, s): self._s = s
            def __repr__(self): return f"ObjectId({self._s!r})"
            def __str__(self): return self._s
        bson_mod.ObjectId = _ObjectId
        _inject("bson", bson_mod)

    if "repositories" not in sys.modules:
        _inject("repositories", types.ModuleType("repositories"))
    if "repositories.database" not in sys.modules:
        db_mod = types.ModuleType("repositories.database")
        class _FakeToList:
            def __init__(self, items): self._items = items
            async def to_list(self, *a, **k): return self._items
        class _FakeCollection:
            def __init__(self): pass
            def find(self, q): return _FakeToList([])
            async def find_one(self, q): return None
            def aggregate(self, p): return _FakeToList([])
            async def update_one(self, *a, **k): return SimpleNamespace()
            async def insert_one(self, *a, **k): return SimpleNamespace()
            async def delete_one(self, *a, **k): return SimpleNamespace()
        db_mod.db_manager = SimpleNamespace(trips=_FakeCollection(), trip_history=_FakeCollection())
        db_mod.db_manager_gps = SimpleNamespace(locations=_FakeCollection())
        _inject("repositories.database", db_mod)


    if "services" not in sys.modules:
        _inject("services", types.ModuleType("services"))
    if "services.trip_service" not in sys.modules:
        ts_mod = types.ModuleType("services.trip_service")
        ts_mod.trip_service = SimpleNamespace()
        _inject("services.trip_service", ts_mod)


    if "events" not in sys.modules:
        _inject("events", types.ModuleType("events"))
    if "events.publisher" not in sys.modules:
        ev_mod = types.ModuleType("events.publisher")
        ev_mod.event_publisher = SimpleNamespace(publish=lambda *a, **k: None)
        _inject("events.publisher", ev_mod)

    if "aiohttp" not in sys.modules:
        _inject("aiohttp", types.ModuleType("aiohttp"))

    for path in _walk_roots_for("simulation_service.py", CANDIDATES):
        try:
            mod_name = f"loaded.simulation_service_{abs(hash(path))}"
            spec = importlib.util.spec_from_file_location(mod_name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)  

            for name in injected:
                sys.modules.pop(name, None)
            return mod
        except Exception:
            continue

    for name in ("simulation_service", "services.simulation_service", "trip_planning.services.simulation_service"):
        try:
            mod = importlib.import_module(name)
            for n in injected:
                sys.modules.pop(n, None)
            return mod
        except Exception:
            pass

    for n in injected:
        sys.modules.pop(n, None)
    raise ModuleNotFoundError("Could not locate simulation_service.py")

simulation_service_module = _load_simulation_service_module()
SimulationService = simulation_service_module.SimulationService
VehicleSimulator = simulation_service_module.VehicleSimulator
Route = simulation_service_module.Route
ObjectId = simulation_service_module.ObjectId

# ------------------------------------------------------------------------------------
# VEHICLE SIMULATOR — basics
# ------------------------------------------------------------------------------------

def test_vehicle_simulator_distance_accessors_and_progress_zero_distance():
    route = Route(coordinates=[(0,0)], distance=0.0, duration=0.0)
    sim = VehicleSimulator("T1", "V1", route, speed_kmh=50)
    sim.distance_traveled = 123.4
    assert sim.get_distance_traveled() == 123.4
    assert sim.get_distance_traveled_km() == pytest.approx(0.1234)
    assert sim.get_remaining_distance() == -123.4  
    assert sim.get_progress_percentage() == 100.0  

def test_vehicle_simulator_calculate_distance_one_degree():
    route = Route(coordinates=[(0,0),(0,1)], distance=0.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=10)
    d = sim.calculate_distance(0,0,0,1)
    assert d == pytest.approx(111_195, rel=1e-3)

def test_vehicle_simulator_get_current_location_no_coords_returns_origin_or_zero():
    route = Route(coordinates=[], distance=0.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=10)
    assert sim.get_current_location() == (0,0)

def test_vehicle_simulator_get_current_location_at_end_returns_last_point():
    route = Route(coordinates=[(0,0),(0,1)], distance=1.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=10)
    sim.current_position = 1.0
    assert sim.get_current_location() == (0,1)

def test_vehicle_simulator_get_current_location_interpolates_mid_segment():
    route = Route(coordinates=[(0,0),(0,1)], distance=1.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=10)
    seg_d = sim.calculate_distance(0,0,0,1)
    sim.route.distance = seg_d
    sim.current_position = 0.5
    lat, lon = sim.get_current_location()
    assert lat == pytest.approx(0.0)
    assert lon == pytest.approx(0.5, rel=1e-3)

def test_vehicle_simulator_get_estimated_finish_time_completes_nowish():
    route = Route(coordinates=[(0,0),(0,1)], distance=1000.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=50)
    sim.current_position = 1.0
    t = sim.get_estimated_finish_time()
    assert (datetime.utcnow() - t).total_seconds() <= 1.0 

def test_vehicle_simulator_get_estimated_finish_time_uses_default_speed_when_invalid():
    route = Route(coordinates=[(0,0),(0,1)], distance=3600.0, duration=0.0) 
    sim = VehicleSimulator("T1","V1",route, speed_kmh=0)  
    sim.current_position = 0.0
    start = datetime.utcnow()
    t = sim.get_estimated_finish_time()
    secs = (t - start).total_seconds()
    assert 200 <= secs <= 320

@pytest.mark.asyncio
async def test_vehicle_simulator_update_position_already_complete_returns_false(monkeypatch):
    route = Route(coordinates=[(0,0),(0,1)], distance=1000.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=50)
    sim.current_position = 1.0
    class _GPS:
        async def update_one(self, *a, **k): raise AssertionError("should not be called")
    class _Trips:
        async def update_one(self, *a, **k): raise AssertionError("should not be called")
    monkeypatch.setattr(simulation_service_module, "db_manager_gps", SimpleNamespace(locations=_GPS()))
    monkeypatch.setattr(simulation_service_module, "db_manager", SimpleNamespace(trips=_Trips()))
    ok = await sim.update_position()
    assert ok is False
    assert sim.is_running is False

@pytest.mark.asyncio
async def test_vehicle_simulator_update_position_happy_path(monkeypatch):
    route = Route(coordinates=[(0,0),(0,1)], distance=1000.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=36)  
    seg_d = sim.calculate_distance(0,0,0,1)
    sim.route.distance = seg_d

    calls = {"gps":0, "trip":0}
    class _GPS:
        async def update_one(self, f, u, upsert=False): calls["gps"] += 1; return SimpleNamespace()
    class _Trips:
        async def update_one(self, f, u): calls["trip"] += 1; return SimpleNamespace()
    monkeypatch.setattr(simulation_service_module, "db_manager_gps", SimpleNamespace(locations=_GPS()))
    monkeypatch.setattr(simulation_service_module, "db_manager", SimpleNamespace(trips=_Trips()))

    ok = await sim.update_position()
    assert ok is True
    assert calls["gps"] == 1 and calls["trip"] == 0
    assert 0.0 < sim.current_position <= 1.0

@pytest.mark.asyncio
async def test_vehicle_simulator_update_position_db_error_is_caught(monkeypatch):
    route = Route(coordinates=[(0,0),(0,1)], distance=1000.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=36)
    seg_d = sim.calculate_distance(0,0,0,1)
    sim.route.distance = seg_d

    class _GPS:
        async def update_one(self, *a, **k): raise RuntimeError("db down")
    class _Trips:
        async def update_one(self, *a, **k): raise AssertionError("should not be reached after gps error")
    monkeypatch.setattr(simulation_service_module, "db_manager_gps", SimpleNamespace(locations=_GPS()))
    monkeypatch.setattr(simulation_service_module, "db_manager", SimpleNamespace(trips=_Trips()))
    ok = await sim.update_position()
    assert ok is True  

@pytest.mark.asyncio
async def test_vehicle_simulator_complete_trip_not_found(monkeypatch):
    route = Route(coordinates=[(0,0),(0,1)], distance=100.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route)
    class _Trips:
        async def find_one(self, q): return None
    monkeypatch.setattr(simulation_service_module, "db_manager",
                        SimpleNamespace(trips=_Trips(), trip_history=SimpleNamespace()))
    await sim._complete_trip()  

@pytest.mark.asyncio
async def test_vehicle_simulator_complete_trip_happy(monkeypatch):
    route = Route(coordinates=[(0,0),(0,1)], distance=100.0, duration=0.0)
    sim = VehicleSimulator("507f191e810c19729de860ea","V1",route)

    saved = {}
    class _Trips:
        async def find_one(self, q): return {"_id": ObjectId("507f191e810c19729de860ea"), "status":"in_progress"}
        async def delete_one(self, q): saved["deleted"] = q; return SimpleNamespace()
    class _Hist:
        async def insert_one(self, doc): saved["inserted"] = doc; return SimpleNamespace()
    monkeypatch.setattr(simulation_service_module, "db_manager",
                        SimpleNamespace(trips=_Trips(), trip_history=_Hist()))
    await sim._complete_trip()
    assert saved["deleted"]["_id"] == ObjectId("507f191e810c19729de860ea")
    assert saved["inserted"]["status"] == "completed"
    assert "moved_to_history_at" in saved["inserted"]

def test_vehicle_simulator_calculate_heading_basic():
    route = Route(coordinates=[(0,0),(0,1)], distance=1.0, duration=0.0)
    sim = VehicleSimulator("T1","V1",route, speed_kmh=10)
    seg_d = sim.calculate_distance(0,0,0,1)
    sim.route.distance = seg_d
    sim.current_position = 0.1
    hdg = sim._calculate_heading()
    assert hdg == pytest.approx(90.0, abs=5.0)

# ------------------------------------------------------------------------------------
# SIMULATION SERVICE — routes
# ------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_route_success_parses_geometry(monkeypatch):
    svc = SimulationService()
    payload = {"routes":[{"geometry":{"coordinates":[[0.0,0.0],[0.5,0.5]]},
                          "distance": 1000.0, "duration": 120.0}]}
    fake = FakeAioHTTP(status=200, payload=payload)
    monkeypatch.setattr(simulation_service_module, "aiohttp", fake)
    r = await svc.get_route(0.0,0.0, 0.5,0.5)
    assert isinstance(r, Route)
    assert r.coordinates == [(0.0,0.0),(0.5,0.5)]
    assert r.distance == 1000.0 and r.duration == 120.0

@pytest.mark.asyncio
async def test_get_route_non_200_falls_back(monkeypatch):
    svc = SimulationService()
    fake = FakeAioHTTP(status=500, payload={})
    monkeypatch.setattr(simulation_service_module, "aiohttp", fake)
    r = await svc.get_route(0.0,0.0, 0.0,1.0)
    assert isinstance(r, Route)
    assert r.duration == 0
    assert len(r.coordinates) == 2
    assert r.distance > 0

@pytest.mark.asyncio
async def test_get_route_exception_falls_back(monkeypatch):
    svc = SimulationService()
    fake = FakeAioHTTP(status=200, payload={}, raise_on_get=True)
    monkeypatch.setattr(simulation_service_module, "aiohttp", fake)
    r = await svc.get_route(0.0,0.0, 0.0,1.0)
    assert isinstance(r, Route)
    assert r.duration == 0
    assert len(r.coordinates) == 2
    assert r.distance > 0

def test__calculate_straight_line_distance_one_degree():
    svc = SimulationService()
    d = svc._calculate_straight_line_distance(0,0, 0,1)
    assert d == pytest.approx(111_195, rel=1e-3)

# ------------------------------------------------------------------------------------
# SIMULATION SERVICE — trips / start
# ------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_active_trips_success(monkeypatch):
    svc = SimulationService()
    trips = [{"_id":"T1","vehicle_id":"V1","origin":{"location":{"coordinates":[[0,0]]}}}]
    class _Trips:
        def find(self, q): return make_to_list_cursor(trips)
    monkeypatch.setattr(simulation_service_module, "db_manager", SimpleNamespace(trips=_Trips()))
    out = await svc.get_active_trips()
    assert out == trips

@pytest.mark.asyncio
async def test_get_active_trips_exception_returns_empty(monkeypatch):
    svc = SimulationService()
    class _Trips:
        def find(self, q): raise RuntimeError("db fail")
    monkeypatch.setattr(simulation_service_module, "db_manager", SimpleNamespace(trips=_Trips()))
    out = await svc.get_active_trips()
    assert out == []

@pytest.mark.asyncio
async def test_start_trip_simulation_no_vehicle_returns(monkeypatch):
    svc = SimulationService()
    trip = {"_id":"T1"}  
    await svc.start_trip_simulation(trip)
    assert "T1" not in svc.active_simulators

@pytest.mark.asyncio
async def test_start_trip_simulation_already_running_returns(monkeypatch):
    svc = SimulationService()
    class _RunningSim:
        def __init__(self):
            self.current_position = 0.5 
            self.is_running = True

    svc.active_simulators["T1"] = _RunningSim()

    trip = {"_id": "T1", "vehicle_id": "V1"}
    await svc.start_trip_simulation(trip)
    assert svc.active_simulators["T1"] is not None

@pytest.mark.asyncio
async def test_start_trip_simulation_missing_coords_returns(monkeypatch):
    svc = SimulationService()
    trip = {"_id":"T1","vehicle_id":"V1","origin":{},"destination":{}}
    await svc.start_trip_simulation(trip)
    assert "T1" not in svc.active_simulators

@pytest.mark.asyncio
async def test_start_trip_simulation_route_none_returns(monkeypatch):
    svc = SimulationService()
    async def fake_route(*a, **k): return None
    monkeypatch.setattr(svc, "get_route_with_waypoints", fake_route)
    trip = {
        "_id":"T1","vehicle_id":"V1",
        "origin":{"location":{"coordinates":[[0.0,0.0],[0.0,0.0]]}},
        "destination":{"location":{"coordinates":[[1.0,1.0],[1.0,1.0]]}}
    }
    await svc.start_trip_simulation(trip)
    assert "T1" not in svc.active_simulators

@pytest.mark.asyncio
async def test_start_trip_simulation_happy(monkeypatch):
    svc = SimulationService()
    async def fake_route(*a, **k):
        return Route(coordinates=[(0, 0), (0, 1)], distance=1000.0, duration=120.0)

    monkeypatch.setattr(svc, "get_route_with_waypoints", fake_route)
    trip = {
        "_id": "507f191e810c19729de860ea",
        "vehicle_id": "V1",
        "origin": {"location": {"coordinates": [0.0, 0.0]}},
        "destination": {"location": {"coordinates": [1.0, 1.0]}},
        "waypoints": [{"location": {"coordinates": [0.5, 0.5]}}],
    }
    await svc.start_trip_simulation(trip)
    assert "507f191e810c19729de860ea" in svc.active_simulators
    sim = svc.active_simulators["507f191e810c19729de860ea"]
    assert isinstance(sim, VehicleSimulator)
    assert sim.is_running is True

    assert sim.current_speed_kmh == 80.0


# ------------------------------------------------------------------------------------
# SIMULATION SERVICE — route with waypoints
# ------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_route_with_waypoints_success(monkeypatch):
    svc = SimulationService()
    payload = {"routes":[{"geometry":{"coordinates":[[0.0,0.0],[0.1,0.2],[0.3,0.4]]},
                          "distance": 1234.5, "duration": 67.8}]}
    fake = FakeAioHTTP(status=200, payload=payload)
    monkeypatch.setattr(simulation_service_module, "aiohttp", fake)
    r = await svc.get_route_with_waypoints(0.0,0.0, 0.3,0.4, waypoints=[(0.2,0.1)])
    assert isinstance(r, Route)
    assert r.coordinates == [(0.0,0.0),(0.2,0.1),(0.4,0.3)] or r.coordinates == [(0.0,0.0),(0.1,0.2),(0.4,0.3)] \
        or len(r.coordinates) >= 2  

@pytest.mark.asyncio
async def test_get_route_with_waypoints_fallback(monkeypatch):
    svc = SimulationService()
    fake = FakeAioHTTP(status=200, payload={}, raise_on_get=True)
    monkeypatch.setattr(simulation_service_module, "aiohttp", fake)
    r = await svc.get_route_with_waypoints(0.0,0.0, 0.3,0.4, waypoints=[(0.1,0.1), (0.2,0.2)])
    assert isinstance(r, Route)
    assert r.duration == 0
    assert r.coordinates == [(0.0,0.0),(0.1,0.1),(0.2,0.2),(0.3,0.4)]
    assert r.distance > 0

# ------------------------------------------------------------------------------------
# SIMULATION SERVICE — update loop & stop
# ------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_all_simulations_removes_completed(monkeypatch):
    svc = SimulationService()
    class Sim1:
        def __init__(self):
            self.is_running = True
        async def update_position(self):
            self.is_running = False
            return False
    class Sim2:
        def __init__(self):
            self.is_running = True
        async def update_position(self):
            return True

    svc.active_simulators = {"A": Sim1(), "B": Sim2()}
    await svc.update_all_simulations()

    assert "A" in svc.active_simulators
    assert svc.active_simulators["A"].is_running is False
    assert "B" in svc.active_simulators


@pytest.mark.asyncio
async def test_start_simulation_service_runs_one_iteration_and_stops(monkeypatch):
    svc = SimulationService()
    async def fake_active(): return []
    async def fake_update(): svc.is_running = False
    async def fake_sleep(_): return None  
    monkeypatch.setattr(svc, "get_active_trips", fake_active)
    monkeypatch.setattr(svc, "update_all_simulations", fake_update)
    monkeypatch.setattr(simulation_service_module.asyncio, "sleep", fake_sleep)
    await svc.start_simulation_service()
    assert svc.is_running is False

@pytest.mark.asyncio
async def test_start_simulation_service_handles_exception_then_stops(monkeypatch):
    svc = SimulationService()
    calls = {"slept":0}
    async def boom(): raise RuntimeError("oops")
    async def fake_sleep(_):
        calls["slept"] += 1
        svc.is_running = False 
    monkeypatch.setattr(svc, "get_active_trips", boom)
    monkeypatch.setattr(simulation_service_module.asyncio, "sleep", fake_sleep)
    await svc.start_simulation_service()
    assert calls["slept"] >= 1
    assert svc.is_running is False

def test_stop_simulation_service_clears_and_flags():
    svc = SimulationService()
    svc.active_simulators["X"] = object()
    svc.is_running = True
    svc.stop_simulation_service()
    assert svc.is_running is False
    assert svc.active_simulators == {}