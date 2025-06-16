from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum

class PluginStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"

class PluginInfo(BaseModel):
    """Plugin information model"""
    plugin_id: str
    name: str
    description: str
    version: str
    docker_service_name: str
    status: PluginStatus
    allowed_roles: List[str]
    port: Optional[int] = None
    health_endpoint: Optional[str] = None

class PluginUpdateRequest(BaseModel):
    """Request model for updating plugin settings"""
    plugin_id: str
    status: Optional[PluginStatus] = None
    allowed_roles: Optional[List[str]] = None

class PluginStatusResponse(BaseModel):
    """Response model for plugin status"""
    plugin_id: str
    status: PluginStatus
    message: str
    container_status: Optional[str] = None
