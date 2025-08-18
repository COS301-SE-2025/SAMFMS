import pytest
from datetime import datetime, timedelta, date
from unittest.mock import AsyncMock
from services.analytics_service import MaintenanceAnalyticsService
import itertools
@pytest.fixture
def svc():
    return MaintenanceAnalyticsService()

@pytest.mark.asyncio
async def test_dashboard_aggregates_counts(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    mocker.object(svc, "license_repo", AsyncMock(), create=True)
    mocker.object(svc, "vendor_repo", AsyncMock(), create=True)
    svc.maintenance_repo.get_overdue_maintenance.return_value = [1,2]
    svc.maintenance_repo.get_upcoming_maintenance.return_value = [1]
    svc.maintenance_repo.get_cost_summary.return_value = {"total_cost": 100, "maintenance_count": 3, "average_cost": 33}
    svc.maintenance_repo.find.return_value = [{"id":"r"}]
    svc.license_repo.get_expiring_soon.return_value = [1]
    svc.license_repo.get_expired_licenses.return_value = [1,2]

    # also patch _get_vehicle_count
    mocker.object(svc, "_get_vehicle_count", new=AsyncMock(return_value=5), create=True)
    res = await svc.get_maintenance_dashboard()
    assert res["overview"]["total_vehicles"] == 5
    assert res["overview"]["overdue_maintenance"] == 2
    assert res["costs"]["total_cost_last_30_days"] == 100
    assert res["recent_activity"] == [{"id":"r"}]

@pytest.mark.asyncio
async def test_cost_analytics_group_by_month_default(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.maintenance_repo.aggregate.side_effect = [[{"_id":{"year":2025,"month":1},"total_cost":10}], [{"total_cost":10}]]
    res = await svc.get_cost_analytics(vehicle_id=None, start_date=None, end_date=None, group_by="month")
    assert res["group_by"] == "month"
    assert res["summary"]["total_cost"] == 10
    assert res["time_series"][0]["_id"]["month"] == 1

@pytest.mark.asyncio
async def test_cost_analytics_group_by_week(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.maintenance_repo.aggregate.side_effect = [[{"_id":{"year":2025,"week":5},"total_cost":7}], [{"total_cost":7}]]
    res = await svc.get_cost_analytics(group_by="week")
    assert "week" in res["time_series"][0]["_id"]

@pytest.mark.asyncio
async def test_trends_calls_aggregate_three_times(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.maintenance_repo.aggregate.return_value = [{"_id":"x","count":1}]
    await svc.get_maintenance_trends(30)
    assert svc.maintenance_repo.aggregate.call_count == 3

@pytest.mark.asyncio
async def test_vendor_analytics_summarizes(mocker, svc):
    mocker.object(svc, "vendor_repo", AsyncMock(), create=True)
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.vendor_repo.get_active_vendors.return_value = [{"id":"v1","name":"ACME"}]
    svc.maintenance_repo.find.return_value = [
        {"actual_cost":100, "actual_start_date":"2025-01-01T00:00:00Z",
         "actual_completion_date":"2025-01-02T00:00:00Z"}
    ]
    res = await svc.get_vendor_analytics()
    assert res["total_vendors"] == 1
    assert res["vendor_performance"][0]["total_cost"] == 100

@pytest.mark.asyncio
async def test_license_analytics_counts_and_aggregate(mocker, svc):
    from unittest.mock import AsyncMock

    def agg_side_effect(*_a, **_k):
        # Provide at least 2 non-empty results, then return [] for further calls
        if not hasattr(agg_side_effect, "calls"):
            agg_side_effect.calls = 0
        agg_side_effect.calls += 1
        if agg_side_effect.calls == 1:
            return [{"_id": "typeA", "count": 5}]
        if agg_side_effect.calls == 2:
            return [{"_id": "entityX", "count": 3}]
        return []

    mocker.object(svc, "license_repo", new=AsyncMock(), create=True)
    svc.license_repo.aggregate = AsyncMock(side_effect=agg_side_effect)
    # Enough counts for expiry_timeline + total_active
    svc.license_repo.count = AsyncMock(side_effect=[1, 2, 3, 4, 10])

    res = await svc.get_license_analytics()
    assert res["licenses_by_type"][0]["_id"] == "typeA"
    assert res["licenses_by_entity"][0]["_id"] == "entityX"
    assert res["total_active_licenses"] == 10

@pytest.mark.asyncio
async def test_total_cost_timeframe_builds_pipeline(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.maintenance_repo.aggregate.return_value = [{"total_cost": 55}]
    res = await svc.get_total_cost_timeframe("2025-01-01T00:00:00Z","2025-01-31T00:00:00Z")
    assert res == 55.0

@pytest.mark.asyncio
async def test_records_count_timeframe_uses_count(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.maintenance_repo.count.return_value = 9
    res = await svc.get_records_count_timeframe("2025-01-01T00:00:00Z","2025-01-31T00:00:00Z")
    assert res == 9

@pytest.mark.asyncio
async def test_vehicles_serviced_timeframe_aggregate(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.maintenance_repo.aggregate.return_value = [{"unique_vehicles": 3}]
    res = await svc.get_vehicles_serviced_timeframe("2025-01-01T00:00:00Z","2025-01-31T00:00:00Z")
    assert res == 3

@pytest.mark.asyncio
async def test_records_by_type_passthrough(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.maintenance_repo.aggregate.return_value = [{"maintenance_type":"t","count":3}]
    res = await svc.get_maintenance_records_by_type()
    assert res[0]["count"] == 3

@pytest.mark.asyncio
async def test_cost_outliers_statistics(mocker, svc):
    from unittest.mock import AsyncMock

    mocker.object(svc, "maintenance_repo", new=AsyncMock(), create=True)
    svc.maintenance_repo.aggregate = AsyncMock(side_effect=[
        [{"average_cost": 100.0, "total_records": 2}],  # must be a list of dicts
        [{"id": "1", "cost": 500.0}],                   # outliers
    ])

    res = await svc.get_maintenance_cost_outliers(threshold_multiplier=2.0)
    assert res["statistics"]["threshold"] == 200.0
    assert res["statistics"]["outlier_count"] == 1

@pytest.mark.asyncio
async def test_cost_by_month_and_type_maps_dict(mocker, svc):
    mocker.object(svc, "maintenance_repo", AsyncMock(), create=True)
    svc.maintenance_repo.aggregate.return_value = [
        {"year_month":"2025-01","maintenance_type":"oil_change","total_cost":50.0}
    ]
    res = await svc.get_cost_by_month_and_type()
    assert res["2025-01"]["oil_change"] == 50.0
