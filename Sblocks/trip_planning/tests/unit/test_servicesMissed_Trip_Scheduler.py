import sys, os, types, importlib, asyncio, pytest

HERE = os.path.abspath(os.path.dirname(__file__))

def _candidate_paths():
    return [
        os.path.abspath(os.path.join(HERE, "..", "..", "services", "missed_trip_scheduler.py")),
        os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "missed_trip_scheduler.py")),
        os.path.abspath(os.path.join(os.getcwd(), "services", "missed_trip_scheduler.py")),
        os.path.abspath(os.path.join(os.getcwd(), "missed_trip_scheduler.py")),
    ]

def _ensure_pkg(name: str):
    if name not in sys.modules:
        m = types.ModuleType(name)
        m.__path__ = [] 
        sys.modules[name] = m
    elif not hasattr(sys.modules[name], "__path__"):
        sys.modules[name].__path__ = []

def _snap(names):
    return {n: sys.modules.get(n) for n in names}

def _restore(snap):
    for n, m in snap.items():
        if m is None:
            sys.modules.pop(n, None)
        else:
            sys.modules[n] = m
    if "services" in snap and snap["services"] is not None and "services.trip_service" in snap:
        setattr(sys.modules["services"], "trip_service", snap["services.trip_service"])


@pytest.fixture(scope="module")
def sched_env():
    names = [
        "services",
        "services.trip_service",
        "services.missed_trip_scheduler",
        "missed_trip_scheduler",
    ]
    snap = _snap(names)

    _ensure_pkg("services")
    trip_mod = types.ModuleType("services.trip_service")

    class _TripService:
        def __init__(self): self.calls = []
        async def mark_missed_trips(self):
            self.calls.append("call")
            return 0

    trip_service = _TripService()
    trip_mod.trip_service = trip_service
    sys.modules["services.trip_service"] = trip_mod
    sys.modules["services"].trip_service = trip_mod

    import importlib.util
    mod = None
    for path in _candidate_paths():
        if os.path.exists(path):
            for name in ("services.missed_trip_scheduler", "missed_trip_scheduler"):
                if name in sys.modules:
                    del sys.modules[name]
            spec = importlib.util.spec_from_file_location("services.missed_trip_scheduler", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.missed_trip_scheduler"] = mod
            spec.loader.exec_module(mod)
            break
    if mod is None:
        _restore(snap)
        raise ImportError("missed_trip_scheduler.py not found")

    env = {
        "module": mod,
        "MissedTripScheduler": mod.MissedTripScheduler,
        "trip_service_stub": trip_service,
    }

    try:
        yield env
    finally:
        try:
            inst = getattr(mod, "missed_trip_scheduler", None)
            if inst and getattr(inst, "running", False):
                async def _stop(inst_):
                    await inst_.stop()
                asyncio.get_event_loop().run_until_complete(_stop(inst))
        except Exception:
            pass
        _restore(snap)

class SleepController:
    def __init__(self):
        self.delays = []
        self._events = []

    def patch(self, monkeypatch):
        orig_sleep = asyncio.sleep

        async def fake_sleep(delay, *a, **k):
            self.delays.append(delay)
            evt = asyncio.Event()
            self._events.append(evt)
            try:
                await evt.wait()
            except asyncio.CancelledError:
                raise

        monkeypatch.setattr(asyncio, "sleep", fake_sleep, raising=True)
        self._tick = orig_sleep  

    async def release_one(self):
        if not self._events:
            return
        self._events.pop(0).set()
        await self._tick(0)

    async def release_all(self):
        while self._events:
            await self.release_one()



def _make(sched_env, **kwargs):
    return sched_env["MissedTripScheduler"](**kwargs)

# ================================== TESTS ==================================

def test_init_defaults_and_custom_interval(sched_env):
    s = _make(sched_env)
    assert s.check_interval_minutes == 5
    assert s.running is False and s._task is None
    s2 = _make(sched_env, check_interval_minutes=1)
    assert s2.check_interval_minutes == 1

@pytest.mark.asyncio
async def test_start_creates_task_and_can_be_stopped(monkeypatch, sched_env, caplog):
    s = _make(sched_env, check_interval_minutes=1)
    calls = []

    async def mark_ok():
        calls.append("ok")
        return 2 

    monkeypatch.setattr(sched_env["module"].trip_service, "mark_missed_trips", mark_ok, raising=True)

    ctrl = SleepController()
    ctrl.patch(monkeypatch)

    await s.start()
    for _ in range(50):
        if calls:
            break
        await ctrl._tick(0)
    assert calls == ["ok"]
    assert s.running is True and s._task is not None

    await s.stop()
    assert s.running is False
    assert s._task.cancelled() or s._task.done()

@pytest.mark.asyncio
async def test_start_when_already_running_warns_and_does_not_replace_task(sched_env, caplog):
    s = _make(sched_env)
    s.running = True
    sentinel = object()
    s._task = sentinel
    with caplog.at_level("WARNING"):
        await s.start()
    assert s._task is sentinel

@pytest.mark.asyncio
async def test_stop_when_not_running_noop(sched_env):
    s = _make(sched_env)
    await s.stop()
    assert s.running is False and s._task is None

@pytest.mark.asyncio
async def test_scheduler_loop_error_path_continues_then_can_be_stopped(monkeypatch, sched_env, caplog):
    s = _make(sched_env, check_interval_minutes=1)
    sequence = ["raise", "ok"]
    seen = []

    async def mark_flaky():
        step = sequence.pop(0)
        seen.append(step)
        if step == "raise":
            raise RuntimeError("boom")
        return 0

    monkeypatch.setattr(sched_env["module"].trip_service, "mark_missed_trips", mark_flaky, raising=True)

    ctrl = SleepController()
    ctrl.patch(monkeypatch)

    await s.start()

    for _ in range(200):
        if 60 in ctrl.delays:
            break
        await ctrl._tick(0)
    assert 60 in ctrl.delays

    await ctrl.release_one()  
    for _ in range(200):
        if seen == ["raise", "ok"]:
            break
        await ctrl._tick(0)
    assert seen == ["raise", "ok"]

    await s.stop()
    assert s.running is False

@pytest.mark.asyncio
async def test_check_now_calls_trip_service_once_and_returns_value(monkeypatch, sched_env):
    s = _make(sched_env)
    called = []
    async def mark_once():
        called.append(1)
        return 3
    monkeypatch.setattr(sched_env["module"].trip_service, "mark_missed_trips", mark_once, raising=True)
    out = await s.check_now()
    assert out == 3 and called == [1]
