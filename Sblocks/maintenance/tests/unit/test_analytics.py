from datetime import datetime
import pytest

from api.routes import analytics as routes


# ---------- Helpers ----------

class _Timer:
    request_id = "req-xyz"
    @property
    def elapsed(self):
        return 7


@pytest.fixture
def fake_timer():
    return _Timer()


@pytest.fixture
def rb_success(mocker):
    def _success(**kwargs):
        return kwargs
    return mocker.patch("api.routes.analytics.ResponseBuilder.success", side_effect=_success)


@pytest.fixture
def rb_error(mocker):
    def _error(**kwargs):
        return kwargs
    return mocker.patch("api.routes.analytics.ResponseBuilder.error", side_effect=_error)


# ---------- /analytics/dashboard ----------

@pytest.mark.asyncio
async def test_get_maintenance_dashboard_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_maintenance_dashboard", return_value={"ok": True})
    res = await routes.get_maintenance_dashboard(user={"user_id": "u"}, timer=fake_timer)
    assert res["data"] == {"ok": True}


@pytest.mark.asyncio
async def test_get_maintenance_dashboard_error(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_maintenance_dashboard", side_effect=Exception("boom"))
    res = await routes.get_maintenance_dashboard(user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /analytics/costs ----------

@pytest.mark.asyncio
async def test_get_cost_analytics_calls_service_with_iso(mocker, rb_success, fake_timer):
    spy = mocker.patch.object(
        routes.maintenance_analytics_service, "get_cost_analytics", return_value={"series": []}
    )
    start = datetime(2024, 1, 1, 12, 30, 0)
    end = datetime(2024, 2, 1, 11, 0, 0)
    await routes.get_cost_analytics(
        vehicle_id="v1",
        start_date=start,
        end_date=end,
        group_by="month",
        user={"user_id": "u"},
        timer=fake_timer
    )
    spy.assert_called_once()
    _, kwargs = spy.call_args
    assert kwargs["vehicle_id"] == "v1"
    assert kwargs["start_date"] == start.isoformat()
    assert kwargs["end_date"] == end.isoformat()
    assert kwargs["group_by"] == "month"


@pytest.mark.asyncio
async def test_get_cost_analytics_error(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_cost_analytics", side_effect=Exception("boom"))
    res = await routes.get_cost_analytics(
        vehicle_id=None, start_date=None, end_date=None, group_by="week", user={"user_id": "u"}, timer=fake_timer
    )
    assert res["status_code"] == 500


# ---------- /analytics/trends ----------

@pytest.mark.asyncio
async def test_get_maintenance_trends_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_maintenance_trends", return_value=[1, 2, 3])
    res = await routes.get_maintenance_trends(days=90, user={"user_id": "u"}, timer=fake_timer)
    assert res["data"] == [1, 2, 3]
    assert res["metadata"]["analysis_period"] == "90 days"


@pytest.mark.asyncio
async def test_get_maintenance_trends_error(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_maintenance_trends", side_effect=Exception("boom"))
    res = await routes.get_maintenance_trends(days=120, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /analytics/vendors ----------

@pytest.mark.asyncio
async def test_get_vendor_analytics_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_vendor_analytics", return_value={"vendors": []})
    res = await routes.get_vendor_analytics(user={"user_id": "u"}, timer=fake_timer)
    assert res["data"] == {"vendors": []}


@pytest.mark.asyncio
async def test_get_vendor_analytics_error(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_vendor_analytics", side_effect=Exception("boom"))
    res = await routes.get_vendor_analytics(user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /analytics/licenses ----------

@pytest.mark.asyncio
async def test_get_license_analytics_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_license_analytics", return_value={"ok": 1})
    res = await routes.get_license_analytics(user={"user_id": "u"}, timer=fake_timer)
    assert res["data"] == {"ok": 1}


@pytest.mark.asyncio
async def test_get_license_analytics_error(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.maintenance_analytics_service, "get_license_analytics", side_effect=Exception("boom"))
    res = await routes.get_license_analytics(user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /analytics/summary/vehicle/{vehicle_id} ----------

@pytest.mark.asyncio
async def test_get_vehicle_maintenance_summary_filters_vehicle_licenses(mocker, rb_success, fake_timer):
    mocker.patch.object(
        routes.maintenance_analytics_service,
        "get_cost_analytics",
        return_value={"costs": [1]},
    )
    mocker.patch.object(
        routes.maintenance_analytics_service,
        "get_license_analytics",
        return_value={
            "licenses_by_entity": [
                {"_id": "vehicle", "count": 5},
                {"_id": "driver", "count": 2},
            ]
        },
    )
    res = await routes.get_vehicle_maintenance_summary(
        vehicle_id="veh-1",
        start_date=datetime(2024, 1, 1, 0, 0, 0),
        end_date=datetime(2024, 2, 1, 0, 0, 0),
        user={"user_id": "u"},
        timer=fake_timer,
    )
    assert res["data"]["vehicle_id"] == "veh-1"
    assert res["data"]["cost_analytics"] == {"costs": [1]}
    assert res["data"]["license_info"] == [{"_id": "vehicle", "count": 5}]
    assert res["data"]["date_range"]["start"].startswith("2024-01-01")


@pytest.mark.asyncio
async def test_get_vehicle_maintenance_summary_error(mocker, rb_error, fake_timer):
    mocker.patch.object(
        routes.maintenance_analytics_service, "get_cost_analytics", side_effect=Exception("boom")
    )
    res = await routes.get_vehicle_maintenance_summary(
        vehicle_id="veh-1", start_date=None, end_date=None, user={"user_id": "u"}, timer=fake_timer
    )
    assert res["status_code"] == 500


# ---------- /analytics/metrics/kpi ----------

@pytest.mark.asyncio
async def test_get_maintenance_kpis_computation(mocker, rb_success, fake_timer):
    mocker.patch.object(
        routes.maintenance_analytics_service,
        "get_maintenance_dashboard",
        return_value={
            "overview": {
                "total_vehicles": 10,
                "overdue_maintenance": 2,
                "upcoming_maintenance": 3,
                "expiring_licenses": 4,
                "expired_licenses": 1,
            },
            "costs": {
                "total_cost_last_30_days": 1000.0,
                "average_cost": 200.0,
                "total_jobs": 5,
            },
        },
    )
    res = await routes.get_maintenance_kpis(user={"user_id": "u"}, timer=fake_timer)
    k = res["data"]
    assert k["operational_kpis"]["overdue_percentage"] == 20.0
    assert k["operational_kpis"]["maintenance_compliance"] == 80.0
    assert k["financial_kpis"]["cost_per_vehicle"] == 100.0
    assert k["compliance_kpis"]["license_compliance_rate"] == 90.0
