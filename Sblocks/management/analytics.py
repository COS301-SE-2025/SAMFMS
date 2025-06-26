from fastapi import APIRouter, HTTPException
from database import (
    vehicle_management_collection,
    vehicle_usage_logs_collection,
    vehicle_assignments_collection,
    fleet_analytics_collection
)

router = APIRouter()

@router.get("/analytics/fleet-utilization")
async def fleet_utilization():
    """Percentage of vehicles with status 'active' vs. total fleet."""
    try:
        total = await vehicle_management_collection.count_documents({})
        active = await vehicle_management_collection.count_documents({"status": "active"})
        utilization_rate = active / total if total else 0
        return {"total": total, "active": active, "utilization_rate": utilization_rate}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch fleet utilization: {e}")

@router.get("/analytics/vehicle-usage")
async def vehicle_usage():
    """Total distance, average trip, fuel consumption per vehicle."""
    try:
        pipeline = [
            {"$group": {
                "_id": "$vehicle_id",
                "total_distance": {"$sum": "$distance_km"},
                "total_fuel": {"$sum": "$fuel_consumed"},
                "trip_count": {"$sum": 1}
            }}
        ]
        stats = await vehicle_usage_logs_collection.aggregate(pipeline).to_list(length=1000)
        for s in stats:
            s["average_trip_length"] = s["total_distance"] / s["trip_count"] if s["trip_count"] else 0
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vehicle usage: {e}")

@router.get("/analytics/assignment-metrics")
async def assignment_metrics():
    """Active/completed assignments, average duration."""
    try:
        active = await vehicle_assignments_collection.count_documents({"status": "active"})
        completed = await vehicle_assignments_collection.count_documents({"status": "completed"})
        pipeline = [
            {"$match": {"end_date": {"$ne": None}}},
            {"$project": {"duration": {"$subtract": ["$end_date", "$start_date"]}}},
            {"$group": {"_id": None, "avg_duration": {"$avg": "$duration"}}}
        ]
        avg = await vehicle_assignments_collection.aggregate(pipeline).to_list(length=1)
        avg_duration = avg[0]["avg_duration"] if avg else 0
        return {"active": active, "completed": completed, "average_duration_ms": avg_duration}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch assignment metrics: {e}")

@router.get("/analytics/maintenance")
async def maintenance_analytics():
    """Vehicles in maintenance, average duration, frequency."""
    try:
        in_maintenance = await vehicle_management_collection.count_documents({"status": "maintenance"})
        freq = await vehicle_assignments_collection.count_documents({"assignment_type": "maintenance"})
        pipeline = [
            {"$match": {"assignment_type": "maintenance", "end_date": {"$ne": None}}},
            {"$project": {"duration": {"$subtract": ["$end_date", "$start_date"]}}},
            {"$group": {"_id": None, "avg_duration": {"$avg": "$duration"}}}
        ]
        avg = await vehicle_assignments_collection.aggregate(pipeline).to_list(length=1)
        avg_duration = avg[0]["avg_duration"] if avg else 0
        return {"in_maintenance": in_maintenance, "maintenance_frequency": freq, "average_duration_ms": avg_duration}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch maintenance analytics: {e}")

@router.get("/analytics/driver-performance")
async def driver_performance():
    """Trips per driver, avg distance, incidents per driver."""
    try:
        pipeline = [
            {"$group": {
                "_id": "$driver_id",
                "trip_count": {"$sum": 1},
                "total_distance": {"$sum": "$distance_km"}
            }}
        ]
        stats = await vehicle_usage_logs_collection.aggregate(pipeline).to_list(length=1000)
        for s in stats:
            s["average_distance"] = s["total_distance"] / s["trip_count"] if s["trip_count"] else 0
        incident_pipeline = [
            {"$match": {"action": "incident"}},
            {"$group": {"_id": "$details.driver_id", "incident_count": {"$sum": 1}}}
        ]
        incidents = await fleet_analytics_collection.aggregate(incident_pipeline).to_list(length=1000)
        incident_map = {i["_id"]: i["incident_count"] for i in incidents}
        for s in stats:
            s["incident_count"] = incident_map.get(s["_id"], 0)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch driver performance: {e}")

@router.get("/analytics/costs")
async def cost_analytics():
    """Total/average cost per vehicle (fuel, maintenance, insurance)."""
    try:
        pipeline = [
            {"$group": {
                "_id": "$vehicle_id",
                "fuel_budget": {"$sum": {"$ifNull": ["$fuel_budget", 0]}},
                "insurance": {"$sum": {"$ifNull": ["$insurance_policy", 0]}},
                "maintenance": {"$sum": {"$ifNull": ["$maintenance_cost", 0]}}
            }}
        ]
        stats = await vehicle_management_collection.aggregate(pipeline).to_list(length=1000)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cost analytics: {e}")

@router.get("/analytics/status-breakdown")
async def status_breakdown():
    """Count of vehicles by status."""
    try:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        stats = await vehicle_management_collection.aggregate(pipeline).to_list(length=100)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch status breakdown: {e}")

@router.get("/analytics/incidents")
async def incident_statistics():
    """Number and type of incidents or alerts reported."""
    try:
        pipeline = [
            {"$match": {"action": "incident"}},
            {"$group": {"_id": "$details.type", "count": {"$sum": 1}}}
        ]
        stats = await fleet_analytics_collection.aggregate(pipeline).to_list(length=100)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch incident statistics: {e}")

@router.get("/analytics/department-location")
async def department_location_analytics():
    """Vehicle usage and costs by department or location."""
    try:
        pipeline = [
            {"$group": {
                "_id": {"department": "$department", "location": "$location"},
                "vehicle_count": {"$sum": 1},
                "total_fuel_budget": {"$sum": {"$ifNull": ["$fuel_budget", 0]}},
                "total_maintenance": {"$sum": {"$ifNull": ["$maintenance_cost", 0]}}
            }}
        ]
        stats = await vehicle_management_collection.aggregate(pipeline).to_list(length=1000)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch department/location analytics: {e}")