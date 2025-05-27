from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from datetime import datetime
from ..models.models import Schedule, ScheduleStatus
from ..services.schedule_service import ScheduleService
from ..messaging.rabbitmq_client import RabbitMQClient
from pydantic import BaseModel


# Request/Response models
class ScheduleCreateRequest(BaseModel):
    trip_id: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    notes: Optional[str] = None


class ScheduleUpdateRequest(BaseModel):
    scheduled_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    notes: Optional[str] = None


class RescheduleRequest(BaseModel):
    new_departure: datetime
    new_arrival: datetime


class ScheduleResponse(BaseModel):
    id: str
    trip_id: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime]
    actual_arrival: Optional[datetime]
    status: ScheduleStatus
    notes: Optional[str]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Dependency to get schedule service
async def get_schedule_service() -> ScheduleService:
    messaging_client = RabbitMQClient()
    await messaging_client.connect()
    return ScheduleService(messaging_client)


router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    schedule_data: ScheduleCreateRequest,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Create a new schedule"""
    try:
        schedule = await schedule_service.create_schedule(schedule_data.dict())
        return ScheduleResponse(
            id=str(schedule.id),
            trip_id=str(schedule.trip_id),
            scheduled_departure=schedule.scheduled_departure,
            scheduled_arrival=schedule.scheduled_arrival,
            actual_departure=schedule.actual_departure,
            actual_arrival=schedule.actual_arrival,
            status=schedule.status,
            notes=schedule.notes,
            cancelled_at=schedule.cancelled_at,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ScheduleResponse])
async def get_schedules(
    status: Optional[ScheduleStatus] = Query(None, description="Filter by schedule status"),
    start_date: Optional[datetime] = Query(None, description="Filter schedules from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter schedules until this date"),
    skip: int = Query(0, ge=0, description="Number of schedules to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of schedules to return"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get schedules with optional filters"""
    try:
        schedules = await schedule_service.get_schedules(
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit
        )
        
        return [
            ScheduleResponse(
                id=str(schedule.id),
                trip_id=str(schedule.trip_id),
                scheduled_departure=schedule.scheduled_departure,
                scheduled_arrival=schedule.scheduled_arrival,
                actual_departure=schedule.actual_departure,
                actual_arrival=schedule.actual_arrival,
                status=schedule.status,
                notes=schedule.notes,
                cancelled_at=schedule.cancelled_at,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at
            )
            for schedule in schedules
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/daily/{date}")
async def get_daily_schedule(
    date: datetime = Path(..., description="Date for daily schedule (YYYY-MM-DD)"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get all schedules for a specific day"""
    try:
        schedules = await schedule_service.get_daily_schedule(date)
        return {
            "date": date.date().isoformat(),
            "schedules": [
                {
                    "id": str(schedule.id),
                    "trip_id": str(schedule.trip_id),
                    "scheduled_departure": schedule.scheduled_departure,
                    "scheduled_arrival": schedule.scheduled_arrival,
                    "status": schedule.status.value,
                    "notes": schedule.notes
                }
                for schedule in schedules
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/driver/{driver_id}")
async def get_driver_schedule(
    driver_id: str = Path(..., description="Driver ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for schedule"),
    end_date: Optional[datetime] = Query(None, description="End date for schedule"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get schedules for a specific driver"""
    try:
        schedules = await schedule_service.get_driver_schedule(
            driver_id=driver_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "driver_id": driver_id,
            "schedules": [
                {
                    "id": str(schedule.id),
                    "trip_id": str(schedule.trip_id),
                    "scheduled_departure": schedule.scheduled_departure,
                    "scheduled_arrival": schedule.scheduled_arrival,
                    "status": schedule.status.value,
                    "notes": schedule.notes
                }
                for schedule in schedules
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/vehicle/{vehicle_id}")
async def get_vehicle_schedule(
    vehicle_id: str = Path(..., description="Vehicle ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for schedule"),
    end_date: Optional[datetime] = Query(None, description="End date for schedule"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get schedules for a specific vehicle"""
    try:
        schedules = await schedule_service.get_vehicle_schedule(
            vehicle_id=vehicle_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "vehicle_id": vehicle_id,
            "schedules": [
                {
                    "id": str(schedule.id),
                    "trip_id": str(schedule.trip_id),
                    "scheduled_departure": schedule.scheduled_departure,
                    "scheduled_arrival": schedule.scheduled_arrival,
                    "status": schedule.status.value,
                    "notes": schedule.notes
                }
                for schedule in schedules
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trip/{trip_id}")
async def get_trip_schedules(
    trip_id: str = Path(..., description="Trip ID"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get all schedules for a specific trip"""
    try:
        schedules = await schedule_service.get_schedules_by_trip(trip_id)
        return {
            "trip_id": trip_id,
            "schedules": [
                {
                    "id": str(schedule.id),
                    "scheduled_departure": schedule.scheduled_departure,
                    "scheduled_arrival": schedule.scheduled_arrival,
                    "actual_departure": schedule.actual_departure,
                    "actual_arrival": schedule.actual_arrival,
                    "status": schedule.status.value,
                    "notes": schedule.notes,
                    "cancelled_at": schedule.cancelled_at
                }
                for schedule in schedules
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str = Path(..., description="Schedule ID"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get a specific schedule by ID"""
    try:
        schedule = await schedule_service.get_schedule_by_id(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
            
        return ScheduleResponse(
            id=str(schedule.id),
            trip_id=str(schedule.trip_id),
            scheduled_departure=schedule.scheduled_departure,
            scheduled_arrival=schedule.scheduled_arrival,
            actual_departure=schedule.actual_departure,
            actual_arrival=schedule.actual_arrival,
            status=schedule.status,
            notes=schedule.notes,
            cancelled_at=schedule.cancelled_at,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdateRequest,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Update a schedule"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in schedule_data.dict().items() if v is not None}
        
        schedule = await schedule_service.update_schedule(schedule_id, update_data)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
            
        return ScheduleResponse(
            id=str(schedule.id),
            trip_id=str(schedule.trip_id),
            scheduled_departure=schedule.scheduled_departure,
            scheduled_arrival=schedule.scheduled_arrival,
            actual_departure=schedule.actual_departure,
            actual_arrival=schedule.actual_arrival,
            status=schedule.status,
            notes=schedule.notes,
            cancelled_at=schedule.cancelled_at,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{schedule_id}/status")
async def update_schedule_status(
    schedule_id: str,
    status: ScheduleStatus,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Update schedule status"""
    try:
        success = await schedule_service.update_schedule_status(schedule_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"message": "Schedule status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{schedule_id}/reschedule", response_model=ScheduleResponse)
async def reschedule(
    schedule_id: str,
    reschedule_data: RescheduleRequest,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Reschedule a trip"""
    try:
        schedule = await schedule_service.reschedule(
            schedule_id=schedule_id,
            new_departure=reschedule_data.new_departure,
            new_arrival=reschedule_data.new_arrival
        )
        
        if not schedule:
            raise HTTPException(status_code=400, detail="Failed to reschedule - conflicts detected")
            
        return ScheduleResponse(
            id=str(schedule.id),
            trip_id=str(schedule.trip_id),
            scheduled_departure=schedule.scheduled_departure,
            scheduled_arrival=schedule.scheduled_arrival,
            actual_departure=schedule.actual_departure,
            actual_arrival=schedule.actual_arrival,
            status=schedule.status,
            notes=schedule.notes,
            cancelled_at=schedule.cancelled_at,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conflicts/check")
async def check_schedule_conflicts(
    driver_id: Optional[str] = Query(None, description="Driver ID to check conflicts for"),
    vehicle_id: Optional[str] = Query(None, description="Vehicle ID to check conflicts for"),
    start_time: datetime = Query(..., description="Start time for conflict check"),
    end_time: datetime = Query(..., description="End time for conflict check"),
    exclude_schedule_id: Optional[str] = Query(None, description="Schedule ID to exclude from conflict check"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Check for scheduling conflicts"""
    try:
        conflicts = await schedule_service.check_schedule_conflicts(
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            start_time=start_time,
            end_time=end_time,
            exclude_schedule_id=exclude_schedule_id
        )
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicts": [
                {
                    "id": str(schedule.id),
                    "trip_id": str(schedule.trip_id),
                    "scheduled_departure": schedule.scheduled_departure,
                    "scheduled_arrival": schedule.scheduled_arrival,
                    "status": schedule.status.value
                }
                for schedule in conflicts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/upcoming/alerts")
async def get_upcoming_schedules(
    hours_ahead: int = Query(24, ge=1, le=168, description="Hours ahead to look for upcoming schedules"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get schedules starting within the specified hours"""
    try:
        schedules = await schedule_service.get_upcoming_schedules(hours_ahead)
        return {
            "upcoming_schedules": [
                {
                    "id": str(schedule.id),
                    "trip_id": str(schedule.trip_id),
                    "scheduled_departure": schedule.scheduled_departure,
                    "scheduled_arrival": schedule.scheduled_arrival,
                    "status": schedule.status.value,
                    "notes": schedule.notes
                }
                for schedule in schedules
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/overdue/alerts")
async def get_overdue_schedules(
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get schedules that are overdue"""
    try:
        schedules = await schedule_service.get_overdue_schedules()
        return {
            "overdue_schedules": [
                {
                    "id": str(schedule.id),
                    "trip_id": str(schedule.trip_id),
                    "scheduled_departure": schedule.scheduled_departure,
                    "scheduled_arrival": schedule.scheduled_arrival,
                    "status": schedule.status.value,
                    "notes": schedule.notes
                }
                for schedule in schedules
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/efficiency")
async def get_schedule_efficiency(
    start_date: Optional[datetime] = Query(None, description="Start date for efficiency analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for efficiency analysis"),
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Get schedule efficiency metrics"""
    try:
        efficiency_metrics = await schedule_service.calculate_schedule_efficiency(
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "efficiency_metrics": efficiency_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    schedule_service: ScheduleService = Depends(get_schedule_service)
):
    """Delete a schedule (cancel)"""
    try:
        success = await schedule_service.delete_schedule(schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"message": "Schedule cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
