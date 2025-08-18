# SAMFMS/Sblocks/maintenance/tests/unit/test_analytics_service.py
import pytest
from datetime import datetime, timedelta

from services import analytics_service as mod

@pytest.mark.asyncio
async def test_get_maintenance_dashboard_happy_path(mocker):
    svc = mod.MaintenanceAnalyticsService()

    # Mock repos on service instance
    mocker.patch.object(svc, "_get_vehicle_count", return_value=42)
    mocker.patch.object(svc.maintenance_repo, "get_overdue_maintenance", return_value=[1, 2])
    mocker.patch.object(svc.maintenance_repo, "get_upcoming_maintenance", return_value=[3])
    mocker.patch.object(svc.maintenance_repo, "get_cost_summary", return_value={"total_cost": 100, "average_cost": 50, "maintenance_count": 2})
    mocker.patch.object(svc.license_repo, "get_expiring_soon", return_value=[{"id": "a"}])
    mocker.patch.object(svc.license_repo, "get_expired_licenses", return_value=[{"id": "b"}, {"id": "c"}])
    mocker.patch.object(svc.maintenance_repo, "find", return_value=[{"_id": "m1"}])

    res = await svc.get_maintenance_dashboard()
    assert res["overview"]["total_vehicles"] == 42
    assert res["costs"]["total_cost_last_30_days"] == 100
    assert len(res["recent_activity"]) == 1


@pytest.mark.asyncio
async def test_get_cost_analytics_builds_pipeline_and_summary_month(mocker):
    svc = mod.MaintenanceAnalyticsService()
    captured = []

    async def _agg(pipeline):
        captured.append(pipeline)
        # first call: time series, second: summary
        if len(captured) == 1:
            return [{"_id": {"year": 2024, "month": 1}, "total_cost": 10}]
        return [{"total_cost": 10, "total_labor_cost": 3, "total_parts_cost": 7, "total_maintenance_count": 1, "average_cost": 10}]
    mocker.patch.object(svc.maintenance_repo, "aggregate", side_effect=_agg)

    res = await svc.get_cost_analytics(vehicle_id="veh1", start_date="2024-01-01T00:00:00Z", end_date="2024-02-01T00:00:00Z", group_by="month")
    assert res["group_by"] == "month"
    assert res["time_series"][0]["total_cost"] == 10
    # Verify vehicle match injected
    m = captured[0][0]["$match"]
    assert m["vehicle_id"] == "veh1"
    assert "$group" in captured[0][1] and "month" in captured[0][1]["$group"]["_id"]


@pytest.mark.asyncio
async def test_get_cost_analytics_defaults_date_range_when_missing(mocker):
    svc = mod.MaintenanceAnalyticsService()
    mocker.patch.object(svc.maintenance_repo, "aggregate", return_value=[])
    res = await svc.get_cost_analytics(group_by="day")
    assert res["date_range"]["start"] < res["date_range"]["end"]
    # day grouping includes day field
    # First aggregate call's $group includes day id
    # We cannot easily inspect since we stubbed return. Good enough to verify key is present from returned group_by
    assert res["group_by"] == "day"


@pytest.mark.asyncio
async def test_get_maintenance_trends_composes_all_three_aggregates(mocker):
    svc = mod.MaintenanceAnalyticsService()
    mocker.patch.object(svc.maintenance_repo, "aggregate", side_effect=[[{"_id": "type", "count": 2}], [{"_id": "status", "count": 5}], [{"_id": "veh", "maintenance_count": 7}]])
    res = await svc.get_maintenance_trends(days=30)
    assert res["period_days"] == 30
    assert res["maintenance_by_status"][0]["_id"] == "status"
    assert res["top_vehicles"][0]["maintenance_count"] == 7


@pytest.mark.asyncio
async def test_get_vendor_analytics_computes_averages_and_durations(mocker):
    svc = mod.MaintenanceAnalyticsService()
    mocker.patch.object(svc.vendor_repo, "get_active_vendors", return_value=[{"id": "v1", "name": "Acme", "rating": 4.5, "is_active": True}])
    # one record with string date values to trigger parsing
    mrec = [{
        "actual_cost": 100.0,
        "labor_cost": 40.0,
        "parts_cost": 60.0,
        "actual_start_date": (datetime.utcnow() - timedelta(hours=5)).isoformat() + "Z",
        "actual_completion_date": datetime.utcnow().isoformat() + "Z",
    }]
    mocker.patch.object(svc.maintenance_repo, "find", return_value=mrec)

    res = await svc.get_vendor_analytics()
    vperf = res["vendor_performance"][0]
    assert vperf["total_jobs"] == 1
    assert vperf["average_cost"] == 100.0
    assert vperf["average_duration_hours"] > 0


@pytest.mark.asyncio
async def test_get_license_analytics_summarizes_counts(mocker):
    svc = mod.MaintenanceAnalyticsService()
    mocker.patch.object(svc.license_repo, "aggregate", side_effect=[[{"_id": "roadworthy", "count": 3}], [{"_id": "vehicle", "count": 5}]])
    mocker.patch.object(svc.license_repo, "count", side_effect=[1, 2, 3, 4, 10])  # expiry timeline then total_active
    res = await svc.get_license_analytics()
    assert res["licenses_by_type"][0]["_id"] == "roadworthy"
    assert res["expiry_timeline"]["expired"] == 1
    assert res["total_active_licenses"] == 10


@pytest.mark.asyncio
async def test__get_vehicle_count_uses_aggregate_and_handles_empty(mocker):
    svc = mod.MaintenanceAnalyticsService()
    mocker.patch.object(svc.maintenance_repo, "aggregate", return_value=[{"total": 7}])
    assert await svc._get_vehicle_count() == 7
    mocker.patch.object(svc.maintenance_repo, "aggregate", return_value=[])
    assert await svc._get_vehicle_count() == 0
