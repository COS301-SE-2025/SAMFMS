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
                docker_service_name="security_service",
                status=PluginStatus.ACTIVE,
                allowed_roles=["admin", "fleet_manager", "driver"],
                port=8007,
                health_endpoint="/health"
            ),
            "gps": PluginInfo(
                plugin_id="gps",
                name="GPS Tracking",
                description="Vehicle location tracking and management",
                version="1.0.0",
                docker_service_name="gps_service",
                status=PluginStatus.INACTIVE,
                allowed_roles=["admin", "fleet_manager"],
                port=8001,
                health_endpoint="/health"
            ),
            "management": PluginInfo(
                plugin_id="management",
                name="Fleet Management",
                description="Vehicle and fleet management operations",
                version="1.0.0",
                docker_service_name="management_service",
                status=PluginStatus.INACTIVE,
                allowed_roles=["admin", "fleet_manager"],
                port=8010,
                health_endpoint="/health"
            ),
            "vehicle_maintenance": PluginInfo(
                plugin_id="vehicle_maintenance",
                name="Vehicle Maintenance",
                description="Vehicle maintenance scheduling and tracking",
                version="1.0.0",
                docker_service_name="vehicle_maintenance_service",
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
                docker_service_name="trip_planning_service",
                status=PluginStatus.INACTIVE,
                allowed_roles=["admin", "fleet_manager", "driver"],
                port=8002,
                health_endpoint="/health"
            ),
            "utilities": PluginInfo(
                plugin_id="utilities",
                name="Utilities Service",
                description="Utility functions and helper services",
                version="1.0.0",
                docker_service_name="utilities_service",                status=PluginStatus.INACTIVE,
                allowed_roles=["admin", "fleet_manager"],
                port=8006,
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
                self._docker_client = False  # Mark as failed to avoid retrying        return self._docker_client if self._docker_client is not False else None
    
    async def get_database(self):
        """Get database connection"""
        if self._db is None:
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
            
            logger.info(f"Initializing {len(self.available_plugins)} plugins in database")
            
            # Initialize each plugin in database if not exists
            for plugin_id, plugin_info in self.available_plugins.items():
                existing = await plugins_collection.find_one({"plugin_id": plugin_id})
                if not existing:
                    plugin_dict = plugin_info.dict()
                    await plugins_collection.insert_one(plugin_dict)
                    logger.info(f"Initialized new plugin: {plugin_id} with status {plugin_dict['status']}")
                else:
                    # Update plugin info but preserve status and roles
                    update_data = plugin_info.dict()
                    update_data["status"] = existing.get("status", plugin_info.status)
                    update_data["allowed_roles"] = existing.get("allowed_roles", plugin_info.allowed_roles)
                    
                    await plugins_collection.update_one(
                        {"plugin_id": plugin_id},
                        {"$set": update_data}
                    )
                    logger.info(f"Updated existing plugin: {plugin_id} with status {update_data['status']}")
                    
            # Count total plugins in database
            total_count = await plugins_collection.count_documents({})
            logger.info(f"Plugin registry initialized - {total_count} plugins total in database")
            
            # Synchronize plugin status with actual container status
            await self.sync_plugin_status()
            
        except Exception as e:
            logger.error(f"Error initializing plugins: {e}")

    async def sync_plugin_status(self):
        """Synchronize plugin status in database with actual Docker container status"""
        try:
            docker_client = self.get_docker_client()
            if not docker_client:
                logger.warning("Docker client not available - skipping status sync")
                return
                
            plugins_collection = await self.get_plugins_collection()
            
            for plugin_id, plugin_info in self.available_plugins.items():
                try:
                    # Check actual container status
                    container_status = self.get_container_status(plugin_info.docker_service_name)
                    
                    # Determine plugin status based on container status
                    if container_status == "running":
                        new_status = PluginStatus.ACTIVE
                    elif container_status in ["exited", "stopped"]:
                        new_status = PluginStatus.INACTIVE
                    elif container_status == "not_found":
                        # For core services like security that should be running, mark as error if not found
                        if plugin_id == "security":
                            new_status = PluginStatus.ERROR
                        else:
                            new_status = PluginStatus.INACTIVE
                    else:
                        new_status = PluginStatus.INACTIVE
                    
                    # Update status in database
                    await plugins_collection.update_one(
                        {"plugin_id": plugin_id},
                        {"$set": {"status": new_status}}
                    )
                    
                    logger.info(f"Synced plugin {plugin_id} status: {new_status} (container: {container_status})")
                    
                except Exception as e:
                    logger.error(f"Error syncing status for plugin {plugin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error syncing plugin status: {e}")
    
    async def get_all_plugins(self) -> List[PluginInfo]:
        """Get all available plugins"""
        try:
            plugins_collection = await self.get_plugins_collection()
            plugins_cursor = plugins_collection.find({})
            plugins = []
            
            async for plugin_doc in plugins_cursor:
                plugin_doc.pop("_id", None)  # Remove MongoDB _id
                plugins.append(PluginInfo(**plugin_doc))
                
            logger.info(f"Found {len(plugins)} plugins in database")
            for plugin in plugins:
                logger.info(f"Plugin: {plugin.plugin_id}, Status: {plugin.status}")
                
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
            result = await plugins_collection.update_one(
                {"plugin_id": plugin_id},
                {"$set": {"allowed_roles": allowed_roles}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating plugin roles: {e}")
            return False
    
    def get_container_status(self, service_name: str) -> Optional[str]:
        """Get Docker container status for a Docker Compose service"""
        try:
            docker_client = self.get_docker_client()
            if not docker_client:
                logger.warning("Docker client not available for container status check")
                return None
            
            # Docker Compose creates containers with project prefix
            # Look for containers with the service name (either exact match or with project prefix)
            containers = docker_client.containers.list(all=True)
            
            for container in containers:                # Check if container name contains the service name
                if service_name in container.name or any(service_name in label for label in container.labels.values()):
                    return container.status
                    
            # If no exact match, try finding by compose service label
            containers_with_labels = docker_client.containers.list(
                all=True, 
                filters={"label": f"com.docker.compose.service={service_name}"}
            )
            
            if containers_with_labels:
                return containers_with_labels[0].status
                
            return "not_found"
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
                
                # Look for container by service name (Docker Compose naming convention)
                service_name = plugin.docker_service_name
                project_name = "samfms"  # Default docker-compose project name
                
                # Try different possible container names
                possible_names = [
                    f"{project_name}-{service_name}-1",
                    f"{project_name}_{service_name}_1", 
                    f"{service_name}-1",
                    f"{service_name}_1",
                    service_name
                ]
                
                container = None
                for name in possible_names:
                    try:
                        container = docker_client.containers.get(name)
                        logger.info(f"Found container: {name}")
                        break
                    except docker.errors.NotFound:
                        continue
                
                if not container:
                    # If no container found, try to create it using docker-compose
                    logger.info(f"No existing container found for {service_name}, attempting to start with compose")
                    
                    # Try to use docker-compose through subprocess
                    try:
                        import subprocess
                        import os
                        
                        # Use docker-compose to start the service
                        compose_cmd = [
                            "docker-compose", "-p", project_name, 
                            "up", "-d", service_name
                        ]
                        
                        # Try to find docker-compose.yml
                        compose_file = "/app/docker-compose.yml"
                        if not os.path.exists(compose_file):
                            compose_file = "/docker-compose.yml"
                        if not os.path.exists(compose_file):
                            compose_file = "../docker-compose.yml"
                        
                        if os.path.exists(compose_file):
                            compose_cmd.extend(["-f", compose_file])
                        
                        result = subprocess.run(
                            compose_cmd,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        
                        if result.returncode == 0:
                            # Wait and try to find the container again
                            import asyncio
                            await asyncio.sleep(3)
                            
                            for name in possible_names:
                                try:
                                    container = docker_client.containers.get(name)
                                    logger.info(f"Found container after compose start: {name}")
                                    break
                                except docker.errors.NotFound:
                                    continue
                        else:
                            logger.error(f"Docker compose failed: {result.stderr}")
                    
                    except Exception as compose_error:
                        logger.error(f"Docker compose error: {compose_error}")
                
                if container:
                    if container.status == "running":
                        await self.update_plugin_status(plugin_id, PluginStatus.ACTIVE)
                        return PluginStatusResponse(
                            plugin_id=plugin_id,
                            status=PluginStatus.ACTIVE,
                            message="Plugin is already running",
                            container_status="running"
                        )
                    else:
                        # Start the existing container
                        try:
                            container.start()
                            
                            # Wait for container to start
                            import asyncio
                            await asyncio.sleep(3)
                            
                            # Check if it started
                            container.reload()
                            if container.status == "running":
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
                                    message=f"Container failed to start, status: {container.status}",
                                    container_status=container.status
                                )
                        except Exception as start_error:
                            await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                            return PluginStatusResponse(
                                plugin_id=plugin_id,
                                status=PluginStatus.ERROR,
                                message=f"Failed to start container: {str(start_error)}",
                                container_status="start_failed"
                            )
                else:
                    await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.ERROR,
                        message="Container not found. Please ensure the service is built with docker-compose.",
                        container_status="not_found"
                    )
                    
            except Exception as docker_error:
                logger.error(f"Docker error in start_plugin: {docker_error}")
                await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message=f"Failed to start plugin: {str(docker_error)}",
                    container_status="error"
                )
                
        except Exception as e:
            logger.error(f"Error starting plugin {plugin_id}: {e}")
            return PluginStatusResponse(
                plugin_id=plugin_id,
                status=PluginStatus.ERROR,
                message=f"Error starting plugin: {str(e)}"            )
    
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
                
                container = self.find_plugin_container(docker_client, plugin.docker_service_name)
                
                if container:
                    if container.status == "running":
                        container.stop()
                        
                        # Wait a moment for the container to stop
                        import time
                        time.sleep(2)
                        
                        # Check if it actually stopped
                        container.reload()
                        await self.update_plugin_status(plugin_id, PluginStatus.INACTIVE)
                        return PluginStatusResponse(
                            plugin_id=plugin_id,
                            status=PluginStatus.INACTIVE,
                            message="Plugin stopped successfully",
                            container_status=container.status
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

    def find_plugin_container(self, docker_client, service_name: str):
        """Find container for a plugin service using multiple strategies"""
        try:
            # Strategy 1: Find by Docker Compose service label
            containers = docker_client.containers.list(
                all=True, 
                filters={"label": f"com.docker.compose.service={service_name}"}
            )
            
            if containers:
                return containers[0]
            
            # Strategy 2: Find by container name containing service name
            all_containers = docker_client.containers.list(all=True)
            for container in all_containers:
                if service_name in container.name:
                    return container
            
            # Strategy 3: Find by project and service (for newer Docker Compose)
            project_containers = docker_client.containers.list(
                all=True,
                filters={"label": "com.docker.compose.project=samfms"}
            )
            
            for container in project_containers:
                labels = container.labels
                if labels.get("com.docker.compose.service") == service_name:
                    return container
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding container for service {service_name}: {e}")
            return None
    
    async def check_plugin_health(self, plugin: PluginInfo) -> bool:
        """Check if a plugin service is healthy by testing its health endpoint"""
        try:
            import httpx
            import asyncio
            
            health_url = f"http://localhost:{plugin.port}{plugin.health_endpoint}"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                return response.status_code == 200
                
        except Exception as e:
            logger.debug(f"Health check failed for plugin {plugin.plugin_id}: {e}")
            return False
    
    async def get_plugin_runtime_status(self, plugin_id: str) -> Dict[str, str]:
        """Get comprehensive runtime status of a plugin"""
        try:
            plugin = await self.get_plugin(plugin_id)
            if not plugin:
                return {"status": "not_found", "container_status": "not_found", "health": "unknown"}
            
            docker_client = self.get_docker_client()
            if not docker_client:
                return {"status": "docker_unavailable", "container_status": "docker_unavailable", "health": "unknown"}
            
            container = self.find_plugin_container(docker_client, plugin.docker_service_name)
            
            if not container:
                return {"status": "container_not_found", "container_status": "not_found", "health": "unreachable"}
            
            container_status = container.status
            health_status = "unknown"
            
            if container_status == "running":
                is_healthy = await self.check_plugin_health(plugin)
                health_status = "healthy" if is_healthy else "unhealthy"
            else:
                health_status = "unreachable"
            
            return {
                "status": "running" if container_status == "running" else "stopped",
                "container_status": container_status,
                "health": health_status,
                "container_id": container.short_id,
                "container_name": container.name
            }
            
        except Exception as e:
            logger.error(f"Error getting runtime status for plugin {plugin_id}: {e}")
            return {"status": "error", "container_status": "error", "health": "error"}

# Global plugin manager instance
plugin_manager = PluginManager()
