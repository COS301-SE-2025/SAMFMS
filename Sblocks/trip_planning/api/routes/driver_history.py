"""
Driver History API routes for Trip Planning service
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from schemas.entities import DriverHistory
from services.driver_history_service import DriverHistoryService
from repositories.database import db_manager, db_manager_management
from services.driver_history_scheduler import get_scheduler

logger = logging.getLogger(__name__)

router = APIRouter()


def get_driver_history_service() -> DriverHistoryService:
    """Dependency to get driver history service instance"""
    return DriverHistoryService(db_manager, db_manager_management)


@router.get("/driver-history/{driver_id}", response_model=dict)
async def get_driver_history(
    driver_id: str,
    service: DriverHistoryService = Depends(get_driver_history_service)
):
    """
    Get comprehensive driver history and statistics
    
    Args:
        driver_id: ID of the driver
        
    Returns:
        Driver history with statistics and metrics
    """
    try:
        logger.info(f"Getting driver history for driver: {driver_id}")
        
        # Get comprehensive driver statistics
        stats = await service.get_driver_statistics(driver_id)
        
        if "error" in stats:
            raise HTTPException(
                status_code=404,
                detail=f"Driver history not found for driver {driver_id}"
            )
        
        return {
            "success": True,
            "message": "Driver history retrieved successfully",
            "data": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting driver history for {driver_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve driver history"
        )


@router.get("/driver-history", response_model=dict)
async def get_all_driver_histories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level (low/medium/high)"),
    service: DriverHistoryService = Depends(get_driver_history_service)
):
    """
    Get all driver histories with optional filtering and pagination
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        risk_level: Optional filter by risk level
        
    Returns:
        List of driver histories with pagination info
    """
    try:
        logger.info(f"Getting driver histories with skip={skip}, limit={limit}, risk_level={risk_level}")
        
        # Validate risk level if provided
        if risk_level and risk_level.lower() not in ['low', 'medium', 'high']:
            raise HTTPException(
                status_code=400,
                detail="Invalid risk level. Must be 'low', 'medium', or 'high'"
            )
        
        # Get driver histories
        histories = await service.get_all_driver_histories(
            skip=skip,
            limit=limit,
            risk_level=risk_level
        )
        
        # Convert to dictionaries for response
        history_data = []
        for history in histories:
            history_dict = history.model_dump(by_alias=True)
            history_data.append(history_dict)
        
        return {
            "success": True,
            "message": f"Retrieved {len(history_data)} driver histories",
            "data": {
                "histories": history_data,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "count": len(history_data),
                    "has_more": len(history_data) == limit
                },
                "filters": {
                    "risk_level": risk_level
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting driver histories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve driver histories"
        )


@router.get("/driver-history/{driver_id}/summary", response_model=dict)
async def get_driver_summary(
    driver_id: str,
    service: DriverHistoryService = Depends(get_driver_history_service)
):
    """
    Get a concise summary of driver performance
    
    Args:
        driver_id: ID of the driver
        
    Returns:
        Concise driver performance summary
    """
    try:
        logger.info(f"Getting driver summary for driver: {driver_id}")
        
        # Get driver history
        history = await service.get_driver_history(driver_id)
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"Driver history not found for driver {driver_id}"
            )
        
        # Create summary
        total_violations = (
            history.speeding_violations + 
            history.braking_violations + 
            history.acceleration_violations + 
            history.phone_usage_violations
        )
        
        summary = {
            "driver_id": driver_id,
            "driver_name": history.driver_name,
            "safety_score": history.driver_safety_score,
            "risk_level": history.driver_risk_level.value,
            "completion_rate": history.trip_completion_rate,
            "total_trips": history.completed_trips,
            "total_violations": total_violations,
            "last_updated": history.last_updated.isoformat()
        }
        
        return {
            "success": True,
            "message": "Driver summary retrieved successfully",
            "data": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting driver summary for {driver_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve driver summary"
        )


@router.post("/driver-history/recalculate", response_model=dict)
async def recalculate_all_histories(
    service: DriverHistoryService = Depends(get_driver_history_service)
):
    """
    Recalculate all driver histories from scratch
    This is useful for data migration or fixing inconsistencies
    
    Returns:
        Summary of recalculation results
    """
    try:
        logger.info("Starting recalculation of all driver histories")
        
        # Perform recalculation
        results = await service.recalculate_all_driver_histories()
        
        return {
            "success": True,
            "message": "Driver histories recalculation completed",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Error recalculating driver histories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to recalculate driver histories"
        )


@router.post("/driver-history/{driver_id}/update", response_model=dict)
async def manual_update_driver_history(
    driver_id: str,
    service: DriverHistoryService = Depends(get_driver_history_service)
):
    """
    Manually trigger an update of a specific driver's history
    
    Args:
        driver_id: ID of the driver to update
        
    Returns:
        Updated driver history summary
    """
    try:
        logger.info(f"Manually updating driver history for driver: {driver_id}")
        
        # Check if driver exists by trying to get current history
        existing_history = await service.get_driver_history(driver_id)
        
        # Trigger recalculation for this specific driver
        await service._recalculate_driver_history(driver_id)
        
        # Get updated statistics
        updated_stats = await service.get_driver_statistics(driver_id)
        
        return {
            "success": True,
            "message": f"Driver history updated successfully for driver {driver_id}",
            "data": updated_stats
        }
        
    except Exception as e:
        logger.error(f"Error manually updating driver history for {driver_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update driver history for driver {driver_id}"
        )


@router.get("/driver-history/analytics/risk-distribution", response_model=dict)
async def get_risk_distribution(
    service: DriverHistoryService = Depends(get_driver_history_service)
):
    """
    Get distribution of drivers by risk level
    
    Returns:
        Risk level distribution analytics
    """
    try:
        logger.info("Getting driver risk distribution analytics")
        
        # Get all histories to calculate distribution
        all_histories = await service.get_all_driver_histories(limit=1000)
        
        # Calculate distribution
        risk_counts = {"low": 0, "medium": 0, "high": 0}
        total_drivers = len(all_histories)
        
        for history in all_histories:
            risk_counts[history.driver_risk_level.value] += 1
        
        # Calculate percentages
        risk_percentages = {}
        for risk_level, count in risk_counts.items():
            risk_percentages[risk_level] = {
                "count": count,
                "percentage": (count / total_drivers * 100) if total_drivers > 0 else 0
            }
        
        return {
            "success": True,
            "message": "Risk distribution retrieved successfully",
            "data": {
                "total_drivers": total_drivers,
                "distribution": risk_percentages
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting risk distribution: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve risk distribution"
        )


@router.get("/driver-history/scheduler/status", response_model=dict)
async def get_scheduler_status():
    """
    Get driver history scheduler status and statistics
    
    Returns:
        Scheduler status with runtime statistics
    """
    try:
        logger.info("Getting driver history scheduler status")
        
        scheduler = get_scheduler()
        
        if scheduler is None:
            return {
                "success": True,
                "message": "Scheduler status retrieved",
                "data": {
                    "status": "not_running",
                    "message": "Driver history scheduler is not running"
                }
            }
        
        stats = scheduler.get_stats()
        
        return {
            "success": True,
            "message": "Scheduler status retrieved successfully",
            "data": {
                "status": "running" if stats["is_running"] else "stopped",
                "statistics": stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve scheduler status"
        )


@router.post("/driver-history/scheduler/force-update", response_model=dict)
async def force_scheduler_update():
    """
    Force an immediate driver history update cycle
    
    Returns:
        Result of the forced update
    """
    try:
        logger.info("Forcing immediate driver history update")
        
        scheduler = get_scheduler()
        
        if scheduler is None:
            raise HTTPException(
                status_code=503,
                detail="Driver history scheduler is not running"
            )
        
        result = await scheduler.force_update()
        
        return {
            "success": result["status"] == "success",
            "message": "Forced update completed" if result["status"] == "success" else f"Forced update failed: {result['message']}",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forcing scheduler update: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to force scheduler update"
        )


@router.get("/driver-history/{driver_id}/trips", response_model=dict)
async def get_driver_trip_history(
    driver_id: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by trip status"),
    service: DriverHistoryService = Depends(get_driver_history_service)
):
    """
    Get trip history for a specific driver
    
    Args:
        driver_id: ID of the driver
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        status: Optional status filter (scheduled, in_progress, completed, cancelled)
        
    Returns:
        List of trips for the driver with trip details and violation counts
    """
    try:
        logger.info(f"Getting trip history for driver: {driver_id}, skip: {skip}, limit: {limit}")
        
        # Get trip history from the trip service
        from services.trip_service import TripService
        trip_service = TripService()
        
        # Build query filter - try both possible field names for driver assignment
        query_filter = {
            "$or": [
                {"driver_assignment": driver_id},
                {"driver_id": driver_id}
            ]
        }
        if status:
            query_filter["status"] = status
        
        # Get trips from database
        trips_collection = db_manager.trips
        
        # Count total trips for pagination
        total_count = await trips_collection.count_documents(query_filter)
        
        # Get trips with pagination, sorted by created_at descending
        cursor = trips_collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        trips = []
        
        async for trip_doc in cursor:
            # Convert ObjectId to string
            if "_id" in trip_doc and trip_doc["_id"]:
                trip_doc["_id"] = str(trip_doc["_id"])
            
            # Get violation counts for this trip
            violation_count = await _get_trip_violation_count(driver_id, str(trip_doc.get("_id", "")))
            
            # Format trip data for frontend
            trip_data = {
                "trip_id": trip_doc.get("_id"),
                "trip_name": trip_doc.get("name", "Unnamed Trip"),
                "scheduled_start_time": trip_doc.get("scheduled_start_time"),
                "scheduled_end_time": trip_doc.get("scheduled_end_time"),
                "actual_start_time": trip_doc.get("actual_start_time"),
                "actual_end_time": trip_doc.get("actual_end_time"),
                "origin": trip_doc.get("origin", {}),
                "destination": trip_doc.get("destination", {}),
                "status": trip_doc.get("status", "unknown"),
                "violation_count": violation_count,
                "estimated_distance": trip_doc.get("estimated_distance"),
                "estimated_duration": trip_doc.get("estimated_duration"),
                "created_at": trip_doc.get("created_at")
            }
            trips.append(trip_data)
        
        return {
            "success": True,
            "data": {
                "trips": trips,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "total_count": total_count,
                    "has_more": (skip + limit) < total_count
                },
                "filters": {
                    "driver_id": driver_id,
                    "status": status
                }
            },
            "message": f"Retrieved {len(trips)} trips for driver {driver_id}"
        }
        
    except Exception as e:
        logger.error(f"Error getting trip history for driver {driver_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trip history: {str(e)}"
        )


async def _get_trip_violation_count(driver_id: str, trip_id: str) -> int:
    """
    Calculate total violation count for a specific trip and driver
    
    Args:
        driver_id: ID of the driver
        trip_id: ID of the trip
        
    Returns:
        Total number of violations for the trip
    """
    try:
        total_violations = 0
        
        # Count speeding violations
        speed_violations = db_manager.speed_violations
        total_violations += await speed_violations.count_documents({
            "driver_id": driver_id,
            "trip_id": trip_id
        })
        
        # Count braking violations
        braking_violations = db_manager.excessive_braking_violations
        total_violations += await braking_violations.count_documents({
            "driver_id": driver_id,
            "trip_id": trip_id
        })
        
        # Count acceleration violations
        acceleration_violations = db_manager.excessive_acceleration_violations
        total_violations += await acceleration_violations.count_documents({
            "driver_id": driver_id,
            "trip_id": trip_id
        })
        
        # Count phone usage violations
        phone_violations = db_manager.driver_ping_violations
        total_violations += await phone_violations.count_documents({
            "driver_id": driver_id,
            "trip_id": trip_id
        })
        
        return total_violations
        
    except Exception as e:
        logger.error(f"Error counting violations for trip {trip_id} and driver {driver_id}: {str(e)}")
        return 0


@router.get("/driver-history/analytics/recent-alerts", response_model=dict)
async def get_recent_driver_alerts(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of alerts to return"),
    hours_back: int = Query(24, ge=1, le=168, description="Number of hours to look back for alerts"),
    service: DriverHistoryService = Depends(get_driver_history_service)
):
    """
    Get recent driver alerts and violations across all drivers
    
    Args:
        limit: Maximum number of alerts to return
        hours_back: Number of hours to look back for alerts
        
    Returns:
        List of recent driver alerts with violation details
    """
    try:
        logger.info(f"Getting recent driver alerts, limit: {limit}, hours_back: {hours_back}")
        
        from datetime import datetime, timedelta
        
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
        
        alerts = []
        
        # Get recent speeding violations
        speed_violations = db_manager.speed_violations
        async for violation in speed_violations.find({
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", -1).limit(limit):
            alerts.append({
                "id": str(violation.get("_id")),
                "type": "speeding",
                "driver_id": violation.get("driver_id"),
                "driver_name": await _get_driver_name(violation.get("driver_id")),
                "severity": "high" if violation.get("speed_over_limit", 0) > 20 else "medium",
                "details": f"Speeding: {violation.get('current_speed', 0)}km/h in {violation.get('speed_limit', 0)}km/h zone",
                "location": violation.get("location", "Unknown location"),
                "timestamp": violation.get("timestamp"),
                "trip_id": violation.get("trip_id")
            })
        
        # Get recent harsh braking violations
        braking_violations = db_manager.excessive_braking_violations
        async for violation in braking_violations.find({
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", -1).limit(limit):
            alerts.append({
                "id": str(violation.get("_id")),
                "type": "harsh_braking",
                "driver_id": violation.get("driver_id"),
                "driver_name": await _get_driver_name(violation.get("driver_id")),
                "severity": "medium",
                "details": f"Harsh braking detected - Deceleration: {violation.get('deceleration', 0):.1f}m/s²",
                "location": violation.get("location", "Unknown location"),
                "timestamp": violation.get("timestamp"),
                "trip_id": violation.get("trip_id")
            })
        
        # Get recent rapid acceleration violations
        acceleration_violations = db_manager.rapid_acceleration_violations
        async for violation in acceleration_violations.find({
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", -1).limit(limit):
            alerts.append({
                "id": str(violation.get("_id")),
                "type": "rapid_acceleration",
                "driver_id": violation.get("driver_id"),
                "driver_name": await _get_driver_name(violation.get("driver_id")),
                "severity": "medium",
                "details": f"Rapid acceleration detected - Acceleration: {violation.get('acceleration', 0):.1f}m/s²",
                "location": violation.get("location", "Unknown location"),
                "timestamp": violation.get("timestamp"),
                "trip_id": violation.get("trip_id")
            })
        
        # Get recent phone usage violations
        phone_violations = db_manager.phone_usage_violations
        async for violation in phone_violations.find({
            "timestamp": {"$gte": time_threshold}
        }).sort("timestamp", -1).limit(limit):
            alerts.append({
                "id": str(violation.get("_id")),
                "type": "phone_usage",
                "driver_id": violation.get("driver_id"),
                "driver_name": await _get_driver_name(violation.get("driver_id")),
                "severity": "high",
                "details": f"Phone usage detected - Duration: {violation.get('duration', 0)}s",
                "location": violation.get("location", "Unknown location"),
                "timestamp": violation.get("timestamp"),
                "trip_id": violation.get("trip_id")
            })
        
        # Sort all alerts by timestamp and limit
        alerts.sort(key=lambda x: x["timestamp"] if x["timestamp"] else datetime.min, reverse=True)
        alerts = alerts[:limit]
        
        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "total_count": len(alerts),
                "time_range": {
                    "hours_back": hours_back,
                    "from": time_threshold.isoformat(),
                    "to": datetime.utcnow().isoformat()
                }
            },
            "message": f"Retrieved {len(alerts)} recent driver alerts"
        }
        
    except Exception as e:
        logger.error(f"Error getting recent driver alerts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent alerts: {str(e)}"
        )


async def _get_driver_name(driver_id: str) -> str:
    """
    Get driver name from driver history or return driver ID
    
    Args:
        driver_id: ID of the driver
        
    Returns:
        Driver name or driver ID if name not found
    """
    try:
        if not driver_id:
            return "Unknown Driver"
            
        # Try to get driver name from driver history
        history_collection = db_manager.driver_history
        history = await history_collection.find_one({"driver_id": driver_id})
        
        if history and history.get("driver_name"):
            return history["driver_name"]
        
        return driver_id
        
    except Exception:
        return driver_id or "Unknown Driver"