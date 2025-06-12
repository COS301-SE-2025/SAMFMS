from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

# Minimal VehicleEventMessage for message queue
class VehicleEventMessage(BaseModel):
    vehicle_id: str
    event_type: str
    data: Dict[str, Any]
    source: str = "vehicle_service"
    timestamp: datetime = None
