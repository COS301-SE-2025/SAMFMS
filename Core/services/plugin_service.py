"""
Plugin management service for SAMFMS
Handles activation/deactivation of Sblocks and role-based access control
"""

import docker
import asyncio
import logging
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.plugin_models import PluginInfo, PluginStatus, PluginStatusResponse
from database import get_database

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugin lifecycle and permissions"""
    
    def __init__(self):
        self._docker_client = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        
        # Default plugin registry - in a real implementation, this could be loaded from config
        self.available_plugins = {
            "security": PluginInfo(
                plugin_id="security",
                name="Security Service",
                description="Authentication and authorization service",
                version="1.0.0",
                docker_service_name="samfms-security-1",
                status=PluginStatus.ACTIVE,
                allowed_roles=["admin", "fleet_manager", "driver"],
                port=8001,
                health_endpoint="/health"
            ),
            "gps": PluginInfo(
                plugin_id="gps",
                name="GPS Tracking",
                description="Vehicle location tracking and management",
                version="1.0.0",
                docker_service_name="samfms-gps-1",
                status=PluginStatus.INACTIVE,
                allowed_roles=["admin", "fleet_manager"],
                port=8002,
                health_endpoint="/health"
            ),
            "management": PluginInfo(
                plugin_id="management",
                name="Fleet Management",
                description="Vehicle and fleet management operations",
                version="1.0.0",
                docker_service_name="samfms-management-1",
                status=PluginStatus.INACTIVE,
                allowed_roles=["admin", "fleet_manager"],
                port=8003,
                health_endpoint="/health"
            ),
            "vehicle_maintenance": PluginInfo(
                plugin_id="vehicle_maintenance",
                name="Vehicle Maintenance",
                description="Vehicle maintenance scheduling and tracking",
                version="1.0.0",
                docker_service_name="samfms-vehicle_maintainence-1",
                status=PluginStatus.INACTIVE,
                allowed_roles=["admin", "fleet_manager"],
                port=8004,
                health_endpoint="/health"
            ),
            "trip_planning": PluginInfo(
                plugin_id="trip_planning",
                name="Trip Planning",
                description="Route optimization and trip planning",
                version="1.0.0",
                docker_service_name="samfms-trip_planning-1",
                status=PluginStatus.INACTIVE,                allowed_roles=["admin", "fleet_manager", "driver"],
                port=8005,
                health_endpoint="/health"
            )
        }

    def get_docker_client(self):
        """Get Docker client with lazy initialization and error handling"""
        if self._docker_client is None:
            try:
                self._docker_client = docker.from_env()
                logger.info("Docker client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Docker client: {e}")
                logger.warning("Plugin management features will be limited without Docker access")
                self._docker_client = False  # Mark as failed to avoid retrying
        return self._docker_client if self._docker_client is not False else None
    
    async def get_database(self):
        """Get database connection"""
        if not self._db:
            self._db = get_database()
        return self._db
    
    async def get_plugins_collection(self):
        """Get plugins collection"""
        db = await self.get_database()
        return db.plugins
    
    async def initialize_plugins(self):
        """Initialize plugin registry in database"""
        try:
            plugins_collection = await self.get_plugins_collection()
            
            # Initialize each plugin in database if not exists
            for plugin_id, plugin_info in self.available_plugins.items():
                existing = await plugins_collection.find_one({"plugin_id": plugin_id})
                if not existing:
                    await plugins_collection.insert_one(plugin_info.dict())
                    logger.info(f"Initialized plugin: {plugin_id}")
                else:
                    # Update plugin info but preserve status and roles
                    update_data = plugin_info.dict()
                    update_data["status"] = existing.get("status", plugin_info.status)
                    update_data["allowed_roles"] = existing.get("allowed_roles", plugin_info.allowed_roles)
                    
                    await plugins_collection.update_one(
                        {"plugin_id": plugin_id},
                        {"$set": update_data}
                    )
                    
            logger.info("Plugin registry initialized")
        except Exception as e:
            logger.error(f"Error initializing plugins: {e}")
    
    async def get_all_plugins(self) -> List[PluginInfo]:
        """Get all available plugins"""
        try:
            plugins_collection = await self.get_plugins_collection()
            plugins_cursor = plugins_collection.find({})
            plugins = []
            
            async for plugin_doc in plugins_cursor:
                plugin_doc.pop("_id", None)  # Remove MongoDB _id
                plugins.append(PluginInfo(**plugin_doc))
                
            return plugins
        except Exception as e:
            logger.error(f"Error getting plugins: {e}")
            return []
    
    async def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get specific plugin by ID"""
        try:
            plugins_collection = await self.get_plugins_collection()
            plugin_doc = await plugins_collection.find_one({"plugin_id": plugin_id})
            
            if plugin_doc:
                plugin_doc.pop("_id", None)
                return PluginInfo(**plugin_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting plugin {plugin_id}: {e}")
            return None
    
    async def update_plugin_status(self, plugin_id: str, status: PluginStatus) -> bool:
        """Update plugin status in database"""
        try:
            plugins_collection = await self.get_plugins_collection()
            result = await plugins_collection.update_one(
                {"plugin_id": plugin_id},
                {"$set": {"status": status}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating plugin status: {e}")
            return False
    
    async def update_plugin_roles(self, plugin_id: str, allowed_roles: List[str]) -> bool:
        """Update plugin allowed roles"""
        try:
            plugins_collection = await self.get_plugins_collection()
            result = await plugins_collection.update_one(                {"plugin_id": plugin_id},
                {"$set": {"allowed_roles": allowed_roles}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating plugin roles: {e}")
            return False
    
    def get_container_status(self, service_name: str) -> Optional[str]:
        """Get Docker container status"""
        try:
            docker_client = self.get_docker_client()
            if not docker_client:
                logger.warning("Docker client not available for container status check")
                return None
                
            containers = docker_client.containers.list(all=True, filters={"name": service_name})
            if containers:
                return containers[0].status
            return None
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return None
    
    async def start_plugin(self, plugin_id: str) -> PluginStatusResponse:
        """Start a plugin (Docker container)"""
        try:
            plugin = await self.get_plugin(plugin_id)
            if not plugin:
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message="Plugin not found"
                )
            
            # Update status to starting
            await self.update_plugin_status(plugin_id, PluginStatus.STARTING)
              # Try to start the container
            try:
                docker_client = self.get_docker_client()
                if not docker_client:
                    await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.ERROR,
                        message="Docker client not available",
                        container_status="docker_unavailable"
                    )
                
                containers = docker_client.containers.list(
                    all=True, 
                    filters={"name": plugin.docker_service_name}
                )
                
                if containers:
                    container = containers[0]
                    if container.status == "running":
                        await self.update_plugin_status(plugin_id, PluginStatus.ACTIVE)
                        return PluginStatusResponse(
                            plugin_id=plugin_id,
                            status=PluginStatus.ACTIVE,
                            message="Plugin is already running",
                            container_status="running"
                        )
                    else:
                        container.start()
                        await self.update_plugin_status(plugin_id, PluginStatus.ACTIVE)
                        return PluginStatusResponse(
                            plugin_id=plugin_id,
                            status=PluginStatus.ACTIVE,
                            message="Plugin started successfully",
                            container_status="running"
                        )
                else:
                    await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.ERROR,
                        message="Container not found",
                        container_status="not_found"
                    )
                    
            except Exception as docker_error:
                await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message=f"Failed to start container: {str(docker_error)}",
                    container_status="error"
                )
                
        except Exception as e:
            logger.error(f"Error starting plugin {plugin_id}: {e}")
            return PluginStatusResponse(
                plugin_id=plugin_id,
                status=PluginStatus.ERROR,
                message=f"Error starting plugin: {str(e)}"
            )
    
    async def stop_plugin(self, plugin_id: str) -> PluginStatusResponse:
        """Stop a plugin (Docker container)"""
        try:
            plugin = await self.get_plugin(plugin_id)
            if not plugin:
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message="Plugin not found"
                )
            
            # Update status to stopping
            await self.update_plugin_status(plugin_id, PluginStatus.STOPPING)
              # Try to stop the container
            try:
                docker_client = self.get_docker_client()
                if not docker_client:
                    await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.ERROR,
                        message="Docker client not available",
                        container_status="docker_unavailable"
                    )
                
                containers = docker_client.containers.list(
                    all=True, 
                    filters={"name": plugin.docker_service_name}
                )
                
                if containers:
                    container = containers[0]
                    if container.status == "running":
                        container.stop()
                        await self.update_plugin_status(plugin_id, PluginStatus.INACTIVE)
                        return PluginStatusResponse(
                            plugin_id=plugin_id,
                            status=PluginStatus.INACTIVE,
                            message="Plugin stopped successfully",
                            container_status="exited"
                        )
                    else:
                        await self.update_plugin_status(plugin_id, PluginStatus.INACTIVE)
                        return PluginStatusResponse(
                            plugin_id=plugin_id,
                            status=PluginStatus.INACTIVE,
                            message="Plugin was already stopped",
                            container_status=container.status
                        )
                else:
                    await self.update_plugin_status(plugin_id, PluginStatus.INACTIVE)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.INACTIVE,
                        message="Container not found",
                        container_status="not_found"
                    )
                    
            except Exception as docker_error:
                await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message=f"Failed to stop container: {str(docker_error)}",
                    container_status="error"
                )
                
        except Exception as e:
            logger.error(f"Error stopping plugin {plugin_id}: {e}")
            return PluginStatusResponse(
                plugin_id=plugin_id,
                status=PluginStatus.ERROR,
                message=f"Error stopping plugin: {str(e)}"
            )
    
    def user_has_plugin_access(self, user_role: str, plugin: PluginInfo) -> bool:
        """Check if user role has access to plugin"""
        return user_role in plugin.allowed_roles

# Global plugin manager instance
plugin_manager = PluginManager()
