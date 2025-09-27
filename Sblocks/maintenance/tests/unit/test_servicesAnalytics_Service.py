import os
import sys
import types
import math
from datetime import datetime, timedelta
import pytest
from unittest.mock import MagicMock, AsyncMock


def _prime_sys_path():
    here = os.path.abspath(os.path.dirname(__file__))
    seen = set()
    for _ in range(12):
        if here in seen:
            break
        seen.add(here)
        if here not in sys.path:
            sys.path.insert(0, here)
        if os.path.isdir(os.path.join(here, "services")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return here

_project_root = _prime_sys_path()

try:
    import repositories as _repositories  
except Exception:
    dummy = types.ModuleType("repositories")
    class _DummyRepo:
        def __init__(self, *args, **kwargs): pass

    for name in ("MaintenanceRecordsRepository","LicenseRecordsRepository","MaintenanceVendorsRepository"):
        setattr(dummy, name, _DummyRepo)
    sys.modules["repositories"] = dummy

_analytics_import_error = None
MaintenanceAnalyticsService = None
for dotted in (
    "services.analytics_service",               
    "maintenance.services.analytics_service",   
    "Sblocks.maintenance.services.analytics_service", 
    "analytics_service",                       
):
    try:
        mod = __import__(dotted, fromlist=["MaintenanceAnalyticsService"])
        MaintenanceAnalyticsService = getattr(mod, "MaintenanceAnalyticsService")
        break
    except Exception as e:
        _analytics_import_error = e

if MaintenanceAnalyticsService is None:
    pytest.skip(f"Cannot import MaintenanceAnalyticsService ({_analytics_import_error}). "
                f"Ensure project root with 'services/analytics_service.py' is on sys.path.")

@pytest.fixture
def svc():
    service = MaintenanceAnalyticsService()
    service.maintenance_repo = getattr(service, "maintenance_repo", MagicMock())
    service.license_repo = getattr(service, "license_repo", MagicMock())
    service.vendor_repo = getattr(service, "vendor_repo", MagicMock())

    def make_async(obj, name):
        if not hasattr(obj, name) or not isinstance(getattr(obj, name), AsyncMock):
            setattr(obj, name, AsyncMock())

    for repo in (service.maintenance_repo, service.license_repo, service.vendor_repo):
        for method in (
            "aggregate","find","count",
            "get_overdue_maintenance","get_upcoming_maintenance","get_cost_summary",
            "get_expiring_soon","get_expired_licenses","get_active_vendors"
        ):
            make_async(repo, method)

    if not hasattr(service, "_get_vehicle_count"):
        setattr(service, "_get_vehicle_count", AsyncMock(return_value=0))

    return service


# ----------------------- get_maintenance_dashboard -----------------------

@pytest.mark.asyncio
async def test_dashboard_success(svc):
    svc._get_vehicle_count = AsyncMock(return_value=5)
    svc.maintenance_repo.get_overdue_maintenance.return_value = [{"_id": "m1"}]
    svc.maintenance_repo.get_upcoming_maintenance.return_value = [{"_id": "m2"}, {"_id": "m3"}]
    svc.maintenance_repo.get_cost_summary.return_value = {"total_cost": 321.5, "average_cost": 160.75, "maintenance_count": 2}
    svc.license_repo.get_expiring_soon.return_value = [1,2,3]
    svc.license_repo.get_expired_licenses.return_value = [9]
    svc.maintenance_repo.find.return_value = [{"_id":"r1"}, {"_id":"r2"}]

    data = await svc.get_maintenance_dashboard()
    assert data["overview"]["total_vehicles"] == 5
    assert data["overview"]["overdue_maintenance"] == 1
    assert data["overview"]["upcoming_maintenance"] == 2
    assert data["overview"]["expiring_licenses"] == 3
    assert data["overview"]["expired_licenses"] == 1
    assert data["costs"]["total_cost_last_30_days"] == 321.5
    assert isinstance(data["recent_activity"], list) and len(data["recent_activity"]) == 2

@pytest.mark.asyncio
async def test_dashboard_error_bubbles(svc):
    svc._get_vehicle_count = AsyncMock(return_value=0)
    svc.maintenance_repo.get_overdue_maintenance.side_effect = RuntimeError("down")
    with pytest.raises(RuntimeError):
        await svc.get_maintenance_dashboard()


# ----------------------- get_cost_analytics -----------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("group_by", ["month","week","day"])
async def test_cost_analytics_success(group_by, svc):
    svc.maintenance_repo.aggregate.side_effect = [
        [{"_id": {"year": 2025, "month": 8} if group_by != "day"
           else {"year": 2025, "month": 8, "day": 21},
          "total_cost": 300.0, "labor_cost": 120.0, "parts_cost": 180.0,
          "maintenance_count": 3, "average_cost": 100.0}],
        [{"_id": None, "total_cost": 300.0, "total_labor_cost": 120.0,
          "total_parts_cost": 180.0, "total_maintenance_count": 3, "average_cost": 100.0}]
    ]
    out = await svc.get_cost_analytics(vehicle_id="V1", start_date=None, end_date=None, group_by=group_by)
    assert out["group_by"] == group_by
    assert out["summary"]["total_cost"] == 300.0
    assert out["time_series"][0]["total_cost"] == 300.0
    assert "start" in out["date_range"] and "end" in out["date_range"]

@pytest.mark.asyncio
async def test_cost_analytics_error_bubbles(svc):
    svc.maintenance_repo.aggregate.side_effect = ValueError("bad agg")
    with pytest.raises(ValueError):
        await svc.get_cost_analytics()


# ----------------------- get_maintenance_trends -----------------------

@pytest.mark.asyncio
async def test_trends_success(svc):
    svc.maintenance_repo.aggregate.side_effect = [
        [{"_id": "oil_change", "count": 5, "avg_cost": 80.0}],    
        [{"_id": "completed", "count": 9}],                      
        [{"_id": "V1", "maintenance_count": 4, "total_cost": 200.0}],  
    ]
    out = await svc.get_maintenance_trends(days=30)
    assert out["period_days"] == 30
    assert out["maintenance_by_type"][0]["_id"] == "oil_change"
    assert out["maintenance_by_status"][0]["_id"] == "completed"
    assert out["top_vehicles"][0]["_id"] == "V1"

@pytest.mark.asyncio
async def test_trends_error_bubbles(svc):
    svc.maintenance_repo.aggregate.side_effect = RuntimeError("fail")
    with pytest.raises(RuntimeError):
        await svc.get_maintenance_trends()


# ----------------------- get_vendor_analytics -----------------------

@pytest.mark.asyncio
async def test_vendor_analytics_success(svc):
    svc.vendor_repo.get_active_vendors.return_value = [{"id": "ven-1", "name": "Best Shop"}]
    now = datetime.utcnow()
    svc.maintenance_repo.find.return_value = [
        {"actual_cost": 200.0, "actual_start_date": (now-timedelta(hours=5)).isoformat(),
         "actual_completion_date": now.isoformat()},
        {"actual_cost": 100.0}
    ]
    out = await svc.get_vendor_analytics()
    perf = out["vendor_performance"][0]
    assert out["total_vendors"] == 1
    assert perf["vendor_id"] == "ven-1"
    assert perf["total_jobs"] == 2
    assert perf["total_cost"] == 300.0
    assert perf["average_duration_hours"] >= 4.9

@pytest.mark.asyncio
async def test_vendor_analytics_none(svc):
    svc.vendor_repo.get_active_vendors.return_value = [{"id": "ven-1", "name": "Best Shop"}]
    svc.maintenance_repo.find.return_value = []
    out = await svc.get_vendor_analytics()
    assert out["vendor_performance"] == []

@pytest.mark.asyncio
async def test_vendor_analytics_error_bubbles(svc):
    svc.vendor_repo.get_active_vendors.side_effect = RuntimeError("down")
    with pytest.raises(RuntimeError):
        await svc.get_vendor_analytics()


# ----------------------- get_license_analytics -----------------------

@pytest.mark.asyncio
async def test_license_analytics_success(svc):
    svc.license_repo.aggregate.side_effect = [
        [{"_id": "roadworthy", "count": 3}],  
        [{"_id": "vehicle", "count": 3}],      
    ]
    svc.license_repo.count.side_effect = [1,2,3,4,9]  
    out = await svc.get_license_analytics()
    assert out["licenses_by_type"][0]["_id"] == "roadworthy"
    assert out["expiry_timeline"]["expired"] == 1
    assert out["total_active_licenses"] == 9

@pytest.mark.asyncio
async def test_license_analytics_error_bubbles(svc):
    svc.license_repo.aggregate.side_effect = RuntimeError("agg err")
    with pytest.raises(RuntimeError):
        await svc.get_license_analytics()


# ----------------------- timeframe helpers -----------------------

@pytest.mark.asyncio
async def test_get_total_cost_timeframe_success(svc):
    svc.maintenance_repo.aggregate.return_value = [{"total_cost": 999.5}]
    total = await svc.get_total_cost_timeframe("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z")
    assert math.isclose(total, 999.5)

@pytest.mark.asyncio
async def test_get_total_cost_timeframe_empty_is_zero(svc):
    svc.maintenance_repo.aggregate.return_value = []
    total = await svc.get_total_cost_timeframe("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z")
    assert total == 0.0

@pytest.mark.asyncio
async def test_get_total_cost_timeframe_error_bubbles(svc):
    svc.maintenance_repo.aggregate.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        await svc.get_total_cost_timeframe("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z")


@pytest.mark.asyncio
async def test_get_records_count_timeframe_success(svc):
    svc.maintenance_repo.count.return_value = 17
    n = await svc.get_records_count_timeframe("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z")
    assert n == 17

@pytest.mark.asyncio
async def test_get_records_count_timeframe_error_bubbles(svc):
    svc.maintenance_repo.count.side_effect = RuntimeError("down")
    with pytest.raises(RuntimeError):
        await svc.get_records_count_timeframe("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z")


@pytest.mark.asyncio
async def test_get_vehicles_serviced_timeframe_success_and_empty(svc):
    svc.maintenance_repo.aggregate.return_value = [{"unique_vehicles": 5}]
    assert await svc.get_vehicles_serviced_timeframe("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z") == 5
    svc.maintenance_repo.aggregate.return_value = []
    assert await svc.get_vehicles_serviced_timeframe("2025-01-01T00:00:00Z", "2025-01-31T23:59:59Z") == 0


# ----------------------- grouping & outliers -----------------------

@pytest.mark.asyncio
async def test_get_maintenance_records_by_type_default_and_with_dates(svc):
    svc.maintenance_repo.aggregate.return_value = [
        {"maintenance_type": "oil_change", "count": 3, "total_cost": 150.0, "average_cost": 50.0}
    ]
    out = await svc.get_maintenance_records_by_type()
    assert out and out[0]["maintenance_type"] == "oil_change"

    svc.maintenance_repo.aggregate.return_value = [
        {"maintenance_type": "brake", "count": 2, "total_cost": 400.0, "average_cost": 200.0}
    ]
    out2 = await svc.get_maintenance_records_by_type("2025-01-01T00:00:00Z","2025-01-31T23:59:59Z")
    assert out2[0]["maintenance_type"] == "brake"


@pytest.mark.asyncio
async def test_get_maintenance_cost_outliers_no_average_returns_empty(svc):
    svc.maintenance_repo.aggregate.side_effect = [
        [],  
    ]
    out = await svc.get_maintenance_cost_outliers()
    assert out["statistics"]["average_cost"] == 0
    assert out["statistics"]["threshold"] == 0
    assert out["outliers"] == []

@pytest.mark.asyncio
async def test_get_maintenance_cost_outliers_with_data(svc):
    svc.maintenance_repo.aggregate.side_effect = [
        [{"average_cost": 100.0, "total_records": 10}],  
        [{"id": "X1", "vehicle_id": "V1", "maintenance_type": "engine",
          "title": "Big Job","cost": 250.0,"created_at": datetime.utcnow().isoformat(),"cost_multiplier": 2.5}]
    ]
    out = await svc.get_maintenance_cost_outliers(threshold_multiplier=2.0)
    assert out["statistics"]["average_cost"] == 100.0
    assert out["statistics"]["threshold"] == 200.0
    assert out["outliers"][0]["id"] == "X1"


# ----------------------- per-vehicle & by-month/type -----------------------

@pytest.mark.asyncio
async def test_get_maintenance_per_vehicle_timeframe_success(svc):
    now = datetime.utcnow().isoformat()
    svc.maintenance_repo.aggregate.return_value = [
        {"vehicle_id":"V1","maintenance_count":3,"total_cost":300.0,
         "average_cost":100.0,"maintenance_types":["oil_change"],"types_count":1,
         "latest_maintenance": now,"earliest_maintenance": now}
    ]
    out = await svc.get_maintenance_per_vehicle_timeframe("2025-01-01T00:00:00Z","2025-01-31T23:59:59Z")
    assert out[0]["vehicle_id"] == "V1"
    assert out[0]["maintenance_count"] == 3

@pytest.mark.asyncio
async def test_get_cost_by_month_and_type_with_and_without_filters(svc):
    svc.maintenance_repo.aggregate.return_value = [
        {"year_month": "2025-08","maintenance_type":"oil_change","total_cost":123.0,"count":2}
    ]
    out = await svc.get_cost_by_month_and_type("2025-08-01T00:00:00Z","2025-08-31T23:59:59Z","V1")
    assert out == {"2025-08": {"oil_change": 123.0}}

    svc.maintenance_repo.aggregate.return_value = [
        {"year_month": "2025-07","maintenance_type":"brake_service","total_cost":500.0,"count":1}
    ]
    out2 = await svc.get_cost_by_month_and_type()
    assert out2["2025-07"]["brake_service"] == 500.0
