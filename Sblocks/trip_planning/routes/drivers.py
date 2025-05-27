from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from datetime import datetime
from ..models.models import Driver, DriverStatus, DriverLicense
from ..services.driver_service import DriverService
from ..messaging.rabbitmq_client import RabbitMQClient
from pydantic import BaseModel, EmailStr


# Request/Response models
class DriverLicenseModel(BaseModel):
    license_number: str
    license_type: DriverLicense
    issue_date: datetime
    expiry_date: datetime
    issuing_authority: str


class DriverCreateRequest(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: datetime
    hire_date: datetime
    license: DriverLicenseModel
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None


class DriverUpdateRequest(BaseModel):
    employee_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    hire_date: Optional[datetime] = None
    license: Optional[DriverLicenseModel] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None


class PerformanceMetricRequest(BaseModel):
    metric_type: str
    value: float
    date: Optional[datetime] = None


class DriverResponse(BaseModel):
    id: str
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: datetime
    hire_date: datetime
    status: DriverStatus
    license: DriverLicenseModel
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    address: Optional[str]
    current_trip_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Dependency to get driver service
async def get_driver_service() -> DriverService:
    messaging_client = RabbitMQClient()
    await messaging_client.connect()
    return DriverService(messaging_client)


router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("/", response_model=DriverResponse)
async def create_driver(
    driver_data: DriverCreateRequest,
    driver_service: DriverService = Depends(get_driver_service)
):
    """Create a new driver"""
    try:
        driver = await driver_service.create_driver(driver_data.dict())
        return DriverResponse(
            id=str(driver.id),
            employee_id=driver.employee_id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            email=driver.email,
            phone=driver.phone,
            date_of_birth=driver.date_of_birth,
            hire_date=driver.hire_date,
            status=driver.status,
            license=DriverLicenseModel(
                license_number=driver.license.license_number,
                license_type=driver.license.license_type,
                issue_date=driver.license.issue_date,
                expiry_date=driver.license.expiry_date,
                issuing_authority=driver.license.issuing_authority
            ),
            emergency_contact_name=driver.emergency_contact_name,
            emergency_contact_phone=driver.emergency_contact_phone,
            address=driver.address,
            current_trip_id=str(driver.current_trip_id) if driver.current_trip_id else None,
            created_at=driver.created_at,
            updated_at=driver.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[DriverResponse])
async def get_drivers(
    status: Optional[DriverStatus] = Query(None, description="Filter by driver status"),
    available_only: bool = Query(False, description="Show only available drivers"),
    skip: int = Query(0, ge=0, description="Number of drivers to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of drivers to return"),
    driver_service: DriverService = Depends(get_driver_service)
):
    """Get drivers with optional filters"""
    try:
        drivers = await driver_service.get_drivers(
            status=status,
            available_only=available_only,
            skip=skip,
            limit=limit
        )
        
        return [
            DriverResponse(
                id=str(driver.id),
                employee_id=driver.employee_id,
                first_name=driver.first_name,
                last_name=driver.last_name,
                email=driver.email,
                phone=driver.phone,
                date_of_birth=driver.date_of_birth,
                hire_date=driver.hire_date,
                status=driver.status,
                license=DriverLicenseModel(
                    license_number=driver.license.license_number,
                    license_type=driver.license.license_type,
                    issue_date=driver.license.issue_date,
                    expiry_date=driver.license.expiry_date,
                    issuing_authority=driver.license.issuing_authority
                ),
                emergency_contact_name=driver.emergency_contact_name,
                emergency_contact_phone=driver.emergency_contact_phone,
                address=driver.address,
                current_trip_id=str(driver.current_trip_id) if driver.current_trip_id else None,
                created_at=driver.created_at,
                updated_at=driver.updated_at
            )
            for driver in drivers
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/available", response_model=List[DriverResponse])
async def get_available_drivers(
    license_types: Optional[List[DriverLicense]] = Query(None, description="Filter by license types"),
    exclude_on_duty: bool = Query(True, description="Exclude drivers currently on duty"),
    driver_service: DriverService = Depends(get_driver_service)
):
    """Get all available drivers for trip assignment"""
    try:
        drivers = await driver_service.get_available_drivers(
            license_types=license_types,
            exclude_on_duty=exclude_on_duty
        )
        
        return [
            DriverResponse(
                id=str(driver.id),
                employee_id=driver.employee_id,
                first_name=driver.first_name,
                last_name=driver.last_name,
                email=driver.email,
                phone=driver.phone,
                date_of_birth=driver.date_of_birth,
                hire_date=driver.hire_date,
                status=driver.status,
                license=DriverLicenseModel(
                    license_number=driver.license.license_number,
                    license_type=driver.license.license_type,
                    issue_date=driver.license.issue_date,
                    expiry_date=driver.license.expiry_date,
                    issuing_authority=driver.license.issuing_authority
                ),
                emergency_contact_name=driver.emergency_contact_name,
                emergency_contact_phone=driver.emergency_contact_phone,
                address=driver.address,
                current_trip_id=str(driver.current_trip_id) if driver.current_trip_id else None,
                created_at=driver.created_at,
                updated_at=driver.updated_at
            )
            for driver in drivers
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
async def search_drivers(
    search_term: str = Query(..., description="Search term for driver name, employee ID, or email"),
    driver_service: DriverService = Depends(get_driver_service)
):
    """Search drivers by name, employee ID, or email"""
    try:
        drivers = await driver_service.search_drivers(search_term)
        return [
            {
                "id": str(driver.id),
                "employee_id": driver.employee_id,
                "first_name": driver.first_name,
                "last_name": driver.last_name,
                "email": driver.email,
                "status": driver.status.value
            }
            for driver in drivers
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: str = Path(..., description="Driver ID"),
    driver_service: DriverService = Depends(get_driver_service)
):
    """Get a specific driver by ID"""
    try:
        driver = await driver_service.get_driver_by_id(driver_id)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
            
        return DriverResponse(
            id=str(driver.id),
            employee_id=driver.employee_id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            email=driver.email,
            phone=driver.phone,
            date_of_birth=driver.date_of_birth,
            hire_date=driver.hire_date,
            status=driver.status,
            license=DriverLicenseModel(
                license_number=driver.license.license_number,
                license_type=driver.license.license_type,
                issue_date=driver.license.issue_date,
                expiry_date=driver.license.expiry_date,
                issuing_authority=driver.license.issuing_authority
            ),
            emergency_contact_name=driver.emergency_contact_name,
            emergency_contact_phone=driver.emergency_contact_phone,
            address=driver.address,
            current_trip_id=str(driver.current_trip_id) if driver.current_trip_id else None,
            created_at=driver.created_at,
            updated_at=driver.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/employee/{employee_id}", response_model=DriverResponse)
async def get_driver_by_employee_id(
    employee_id: str = Path(..., description="Employee ID"),
    driver_service: DriverService = Depends(get_driver_service)
):
    """Get a specific driver by employee ID"""
    try:
        driver = await driver_service.get_driver_by_employee_id(employee_id)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
            
        return DriverResponse(
            id=str(driver.id),
            employee_id=driver.employee_id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            email=driver.email,
            phone=driver.phone,
            date_of_birth=driver.date_of_birth,
            hire_date=driver.hire_date,
            status=driver.status,
            license=DriverLicenseModel(
                license_number=driver.license.license_number,
                license_type=driver.license.license_type,
                issue_date=driver.license.issue_date,
                expiry_date=driver.license.expiry_date,
                issuing_authority=driver.license.issuing_authority
            ),
            emergency_contact_name=driver.emergency_contact_name,
            emergency_contact_phone=driver.emergency_contact_phone,
            address=driver.address,
            current_trip_id=str(driver.current_trip_id) if driver.current_trip_id else None,
            created_at=driver.created_at,
            updated_at=driver.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: str,
    driver_data: DriverUpdateRequest,
    driver_service: DriverService = Depends(get_driver_service)
):
    """Update a driver"""
    try:
        # Filter out None values
        update_data = {k: v for k, v in driver_data.dict().items() if v is not None}
        
        driver = await driver_service.update_driver(driver_id, update_data)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
            
        return DriverResponse(
            id=str(driver.id),
            employee_id=driver.employee_id,
            first_name=driver.first_name,
            last_name=driver.last_name,
            email=driver.email,
            phone=driver.phone,
            date_of_birth=driver.date_of_birth,
            hire_date=driver.hire_date,
            status=driver.status,
            license=DriverLicenseModel(
                license_number=driver.license.license_number,
                license_type=driver.license.license_type,
                issue_date=driver.license.issue_date,
                expiry_date=driver.license.expiry_date,
                issuing_authority=driver.license.issuing_authority
            ),
            emergency_contact_name=driver.emergency_contact_name,
            emergency_contact_phone=driver.emergency_contact_phone,
            address=driver.address,
            current_trip_id=str(driver.current_trip_id) if driver.current_trip_id else None,
            created_at=driver.created_at,
            updated_at=driver.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{driver_id}/status")
async def update_driver_status(
    driver_id: str,
    status: DriverStatus,
    driver_service: DriverService = Depends(get_driver_service)
):
    """Update driver status"""
    try:
        success = await driver_service.update_driver_status(driver_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Driver not found")
        return {"message": "Driver status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{driver_id}/location")
async def update_driver_location(
    driver_id: str,
    location_data: LocationUpdateRequest,
    driver_service: DriverService = Depends(get_driver_service)
):
    """Update driver location"""
    try:
        success = await driver_service.update_driver_location(
            driver_id=driver_id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            timestamp=location_data.timestamp
        )
        if not success:
            raise HTTPException(status_code=404, detail="Driver not found")
        return {"message": "Driver location updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{driver_id}/performance")
async def add_performance_metric(
    driver_id: str,
    metric_data: PerformanceMetricRequest,
    driver_service: DriverService = Depends(get_driver_service)
):
    """Add performance metric for driver"""
    try:
        success = await driver_service.add_driver_performance_metric(
            driver_id=driver_id,
            metric_type=metric_data.metric_type,
            value=metric_data.value,
            date=metric_data.date
        )
        if not success:
            raise HTTPException(status_code=404, detail="Driver not found")
        return {"message": "Performance metric added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{driver_id}/performance")
async def get_driver_performance(
    driver_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for performance summary"),
    end_date: Optional[datetime] = Query(None, description="End date for performance summary"),
    driver_service: DriverService = Depends(get_driver_service)
):
    """Get driver performance summary"""
    try:
        performance_summary = await driver_service.get_driver_performance_summary(
            driver_id=driver_id,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "driver_id": driver_id,
            "performance_summary": performance_summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/license/expiring")
async def get_drivers_with_expiring_licenses(
    days_ahead: int = Query(60, ge=1, le=365, description="Days ahead to check for license expiry"),
    driver_service: DriverService = Depends(get_driver_service)
):
    """Get drivers with licenses expiring soon"""
    try:
        drivers = await driver_service.check_license_expiry(days_ahead)
        return {
            "drivers_with_expiring_licenses": [
                {
                    "id": str(driver.id),
                    "employee_id": driver.employee_id,
                    "first_name": driver.first_name,
                    "last_name": driver.last_name,
                    "license_number": driver.license.license_number,
                    "license_type": driver.license.license_type.value,
                    "expiry_date": driver.license.expiry_date
                }
                for driver in drivers
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{driver_id}")
async def delete_driver(
    driver_id: str,
    driver_service: DriverService = Depends(get_driver_service)
):
    """Delete a driver (soft delete)"""
    try:
        success = await driver_service.delete_driver(driver_id)
        if not success:
            raise HTTPException(status_code=404, detail="Driver not found")
        return {"message": "Driver deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
