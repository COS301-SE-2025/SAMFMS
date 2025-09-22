"""
API routes for excessive acceleration violations
"""
import logging
from typing import Dict, Any
from datetime import datetime
from bson import ObjectId

from fastapi import APIRouter, HTTPException, status
from repositories.database import db_manager
from schemas.entities import ExcessiveAccelerationViolation
from schemas.requests import CreateExcessiveAccelerationViolationRequest
from schemas.responses import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/excessive-acceleration-violations",
    tags=["Excessive Acceleration Violations"]
)


@router.post("/", response_model=StandardResponse)
async def create_excessive_acceleration_violation(
    request: CreateExcessiveAccelerationViolationRequest
) -> StandardResponse:
    """
    Create a new excessive acceleration violation manually
    
    Creates an excessive acceleration violation record with the provided acceleration rate, threshold, location, and time.
    The violation will be associated with a specific trip and driver.
    """
    logger.info(f"[ExcessiveAccelerationViolationAPI] Creating excessive acceleration violation for trip {request.trip_id}, driver {request.driver_id}")
    
    try:
        # Verify the trip exists
        trip_doc = await db_manager.trips.find_one({"_id": ObjectId(request.trip_id)})
        if not trip_doc:
            logger.warning(f"[ExcessiveAccelerationViolationAPI] Trip {request.trip_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip {request.trip_id} not found"
            )
        
        # Verify the driver is assigned to this trip
        if trip_doc.get("driver_assignment") != request.driver_id:
            logger.warning(f"[ExcessiveAccelerationViolationAPI] Driver {request.driver_id} not assigned to trip {request.trip_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Driver {request.driver_id} is not assigned to trip {request.trip_id}"
            )
        
        # Create violation record
        violation_data = {
            "trip_id": request.trip_id,
            "driver_id": request.driver_id,
            "acceleration": request.acceleration,
            "threshold": request.threshold,
            "location": request.location.dict(),
            "time": request.time,
            "created_at": datetime.utcnow()
        }
        
        # Insert into database
        result = await db_manager.excessive_acceleration_violations.insert_one(violation_data)
        violation_data["_id"] = str(result.inserted_id)
        
        # Create response object
        violation = ExcessiveAccelerationViolation(**violation_data)
        
        logger.info(f"[ExcessiveAccelerationViolationAPI] Created excessive acceleration violation {violation.id} for trip {request.trip_id}")
        
        return StandardResponse(
            success=True,
            message="Excessive acceleration violation created successfully",
            data={
                "violation_id": violation.id,
                "trip_id": violation.trip_id,
                "driver_id": violation.driver_id,
                "acceleration": violation.acceleration,
                "threshold": violation.threshold,
                "acceleration_over_threshold": violation.acceleration - violation.threshold,
                "location": violation.location.dict(),
                "time": violation.time.isoformat(),
                "created_at": violation.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ExcessiveAccelerationViolationAPI] Failed to create excessive acceleration violation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create excessive acceleration violation"
        )


@router.get("/trip/{trip_id}", response_model=StandardResponse)
async def get_trip_excessive_acceleration_violations(
    trip_id: str
) -> StandardResponse:
    """
    Get all excessive acceleration violations for a specific trip
    """
    logger.info(f"[ExcessiveAccelerationViolationAPI] Getting excessive acceleration violations for trip {trip_id}")
    
    try:
        # Verify the trip exists
        trip_doc = await db_manager.trips.find_one({"_id": ObjectId(trip_id)})
        if not trip_doc:
            logger.warning(f"[ExcessiveAccelerationViolationAPI] Trip {trip_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip {trip_id} not found"
            )
        
        # Get all excessive acceleration violations for this trip
        cursor = db_manager.excessive_acceleration_violations.find({"trip_id": trip_id}).sort("time", -1)
        violations = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            violations.append(ExcessiveAccelerationViolation(**doc))
        
        violations_data = [
            {
                "violation_id": v.id,
                "driver_id": v.driver_id,
                "acceleration": v.acceleration,
                "threshold": v.threshold,
                "acceleration_over_threshold": v.acceleration - v.threshold,
                "location": v.location.dict(),
                "time": v.time.isoformat(),
                "created_at": v.created_at.isoformat()
            }
            for v in violations
        ]
        
        logger.info(f"[ExcessiveAccelerationViolationAPI] Retrieved {len(violations)} excessive acceleration violations for trip {trip_id}")
        
        return StandardResponse(
            success=True,
            message=f"Retrieved {len(violations)} excessive acceleration violations for trip",
            data={
                "trip_id": trip_id,
                "violations": violations_data,
                "total_violations": len(violations)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ExcessiveAccelerationViolationAPI] Failed to get excessive acceleration violations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve excessive acceleration violations"
        )