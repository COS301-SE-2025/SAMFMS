from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class PluginStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"

class PluginCategory(str, Enum):
    CORE = "core"
    TRACKING = "tracking"
    MANAGEMENT = "management"
    MAINTENANCE = "maintenance"
    PLANNING = "planning"
    UTILITIES = "utilities"

class PluginErrorCode(str, Enum):
    CONTAINER_NOT_FOUND = "CONTAINER_NOT_FOUND"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    START_TIMEOUT = "START_TIMEOUT"
    STOP_TIMEOUT = "STOP_TIMEOUT"
    HEALTH_CHECK_FAILED = "HEALTH_CHECK_FAILED"
    DOCKER_UNAVAILABLE = "DOCKER_UNAVAILABLE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

class PluginDependency(BaseModel):
    """Plugin dependency definition"""
    service_name: str
    required: bool = True
    health_check: Optional[str] = None

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
    health_endpoint: Optional[str] = "/health"
    required: bool = False
    category: PluginCategory = PluginCategory.UTILITIES
    dependencies: List[str] = Field(default_factory=list)
    install_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    config: Dict[str, Any] = Field(default_factory=dict)

class PluginUpdateRequest(BaseModel):
    """Request model for updating plugin settings"""
    plugin_id: str
    status: Optional[PluginStatus] = None
    allowed_roles: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

class PluginStatusResponse(BaseModel):
    """Response model for plugin status"""
    plugin_id: str
    status: PluginStatus
    message: str
    container_status: Optional[str] = None
    error_code: Optional[PluginErrorCode] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PluginOperationRequest(BaseModel):
    """Request model for plugin operations"""
    plugin_id: str
    operation: str  # start, stop, restart
    force: bool = False
    timeout: int = 120

class PluginHealthStatus(BaseModel):
    """Plugin health status model"""
    plugin_id: str
    healthy: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_check: datetime = Field(default_factory=datetime.utcnow)

class PluginError(Exception):
    """Custom plugin exception with error codes"""
    def __init__(self, plugin_id: str, operation: str, error_code: PluginErrorCode, message: str):
        self.plugin_id = plugin_id
        self.operation = operation
        self.error_code = error_code
        super().__init__(message)
