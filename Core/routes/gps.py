from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Dict, Dict
import logging

from models.plugin_models import PluginInfo, PluginUpdateRequest, PluginStatusResponse
from services.plugin_service import plugin_manager

from ..rabbitmq.consumer import consume_messages,consume_messages_Direct
from ..rabbitmq.producer import publish_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gps", tags=["GPS Management"])
security = HTTPBearer()

#@router.post("/geofences/cirlce")