from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import json
import logging
import requests
import os

from models import (
    VehicleAssignment, VehicleUsageLog, VehicleStatus, 
    VehicleAssignmentResponse
)
from auth_utils import (
    require_permission, require_role, get_current_user, 
    filter_data_by_role, can_access_resource
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Vehicle Assignment Routes
