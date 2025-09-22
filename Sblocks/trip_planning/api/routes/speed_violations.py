"""
API routes for speed violations
"""
import logging
from typing import Dict, Any
from datetime import datetime
from bson import ObjectId

from fastapi import APIRouter, HTTPException, status
from repositories.database import db_manager
from schemas.entities import SpeedViolation
from schemas.requests import CreateSpeedViolationRequest
from schemas.responses import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/speed-violations",
    tags=["Speed Violations"]
)


@router.post("/", response_model=StandardResponse)
async def create_speed_violation(
    request: CreateSpeedViolationRequest
) -> StandardResponse:
    """
    Create a new speed violation manually
    
    Creates a speed violation record with the provided speed, speed limit, location, and time.
    The violation will be associated with a specific trip and driver.
    """
    logger.info(f"[SpeedViolationAPI] Creating speed violation for trip {request.trip_id}, driver {request.driver_id}")
    
    try:
        # Verify the trip exists
        trip_doc = await db_manager.trips.find_one({"_id": ObjectId(request.trip_id)})
        if not trip_doc:
            logger.warning(f"[SpeedViolationAPI] Trip {request.trip_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip {request.trip_id} not found"
            )
        
        # Verify the driver is assigned to this trip
        if trip_doc.get("driver_assignment") != request.driver_id:
            logger.warning(f"[SpeedViolationAPI] Driver {request.driver_id} not assigned to trip {request.trip_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Driver {request.driver_id} is not assigned to trip {request.trip_id}"
            )
        
        # Create violation record
        violation_data = {
            "trip_id": request.trip_id,
            "driver_id": request.driver_id,
            "speed": request.speed,
            "speed_limit": request.speed_limit,
            "location": request.location.dict(),
            "time": request.time,
            "created_at": datetime.utcnow()
        }
        
        # Insert into database
        result = await db_manager.speed_violations.insert_one(violation_data)
        violation_data["_id"] = str(result.inserted_id)
        
        # Create response object
        violation = SpeedViolation(**violation_data)
        
        logger.info(f"[SpeedViolationAPI] Created speed violation {violation.id} for trip {request.trip_id}")
        
        return StandardResponse(
            success=True,
            message="Speed violation created successfully",
            data={
                "violation_id": violation.id,
                "trip_id": violation.trip_id,
                "driver_id": violation.driver_id,
                "speed": violation.speed,
                "speed_limit": violation.speed_limit,
                "speed_over_limit": violation.speed - violation.speed_limit,
                "location": violation.location.dict(),
                "time": violation.time.isoformat(),
                "created_at": violation.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SpeedViolationAPI] Failed to create speed violation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create speed violation"
        )


@router.get("/trip/{trip_id}", response_model=StandardResponse)
async def get_trip_speed_violations(
    trip_id: str
) -> StandardResponse:
    """
    Get all speed violations for a specific trip
    """
    logger.info(f"[SpeedViolationAPI] Getting speed violations for trip {trip_id}")
    
    try:
        # Verify the trip exists
        trip_doc = await db_manager.trips.find_one({"_id": ObjectId(trip_id)})
        if not trip_doc:
            logger.warning(f"[SpeedViolationAPI] Trip {trip_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip {trip_id} not found"
            )
        
        # Get all speed violations for this trip
        cursor = db_manager.speed_violations.find({"trip_id": trip_id}).sort("time", -1)
        violations = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            violations.append(SpeedViolation(**doc))
        
        violations_data = [
            {
                "violation_id": v.id,
                "driver_id": v.driver_id,
                "speed": v.speed,
                "speed_limit": v.speed_limit,
                "speed_over_limit": v.speed - v.speed_limit,
                "location": v.location.dict(),
                "time": v.time.isoformat(),
                "created_at": v.created_at.isoformat()
            }
            for v in violations
        ]
        
        logger.info(f"[SpeedViolationAPI] Retrieved {len(violations)} speed violations for trip {trip_id}")
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(violations)} speed violations for trip",
            data={
                "trip_id": trip_id,
                "violations": violations_data,
                "total_violations": len(violations)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SpeedViolationAPI] Failed to get speed violations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve speed violations"
        )