from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Dict, Dict
import logging

from models.plugin_models import PluginInfo, PluginUpdateRequest, PluginStatusResponse
from services.plugin_service import plugin_manager
from auth_service import verify_token, get_current_user_from_token
from rabbitmq.admin import addSblock, removeSblock
from ..database import db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)
security = HTTPBearer()

@router.get("/user/{user_id}")
def get_user_data(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_data = verify_token(credentials)
    if user_data.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's data"
        )
    return {"message": "User data retrieved successfully", "user": user_data}
