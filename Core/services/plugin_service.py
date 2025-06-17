"""
Plugin management service for SAMFMS
Handles activation/deactivation of Sblocks and role-based access control
"""

import docker
import asyncio
import logging
import subprocess
import os
import time
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from models.plugin_models import (
    PluginInfo, PluginStatus, PluginStatusResponse, PluginError, 
    PluginErrorCode, PluginHealthStatus, PluginOperationRequest
)
from database import get_database
from plugin_config import plugin_config_loader

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugin lifecycle and permissions"""
    
    def __init__(self):
        self._docker_client = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._project_dir = self._get_project_directory()
        
    def _get_project_directory(self) -> str:
        """Get the project directory for Docker Compose operations"""
        project_dir = "/project"
        if not os.path.exists(project_dir):
            project_dir = "/app"
        return project_dir

    def get_docker_client(self):
        """Get Docker client with lazy initialization and error handling"""
        if self._docker_client is None:
            try:
                # Try different Docker connection methods
                try:
                    # First try the default (Unix socket)
                    self._docker_client = docker.from_env()
                    # Test the connection
                    self._docker_client.ping()
                    logger.info("Docker client initialized successfully using default connection")
                except Exception as e1:
                    logger.warning(f"Default Docker connection failed: {e1}")
                    try:
                        # Try explicit Unix socket connection
                        self._docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
                        self._docker_client.ping()
                        logger.info("Docker client initialized successfully using Unix socket")
                    except Exception as e2:
                        logger.warning(f"Unix socket connection failed: {e2}")
                        raise Exception(f"All Docker connection methods failed. Default: {e1}, Unix: {e2}")
                        
            except Exception as e:
                logger.error(f"Failed to initialize Docker client: {e}")
                logger.error("Plugin management features will be limited without Docker access")
                logger.error("Make sure Docker socket is properly mounted and accessible")
                self._docker_client = False  # Mark as failed to avoid retrying
        return self._docker_client if self._docker_client is not False else None
    
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
        """Initialize plugin registry in database from configuration"""
        try:
            plugins_collection = await self.get_plugins_collection()
            
            # Load plugin configurations
            plugin_configs = plugin_config_loader.get_all_plugins_config()
            logger.info(f"Initializing {len(plugin_configs)} plugins from configuration")
            
            # Initialize each plugin in database if not exists
            for plugin_id, config in plugin_configs.items():
                try:
                    # Validate configuration
                    if not plugin_config_loader.validate_plugin_config(plugin_id, config):
                        logger.error(f"Invalid configuration for plugin {plugin_id}, skipping")
                        continue
                    
                    # Check if plugin exists in database
                    existing = await plugins_collection.find_one({"plugin_id": plugin_id})
                    
                    # Create plugin info from configuration
                    plugin_info = plugin_config_loader.create_plugin_info(plugin_id, config)
                    
                    if not existing:
                        # Add timestamps for new plugins
                        plugin_dict = plugin_info.dict()
                        plugin_dict["install_date"] = datetime.utcnow()
                        plugin_dict["last_updated"] = datetime.utcnow()
                        
                        await plugins_collection.insert_one(plugin_dict)
                        logger.info(f"Initialized new plugin: {plugin_id} with status {plugin_dict['status']}")
                    else:
                        # Update plugin info but preserve status and custom settings
                        update_data = plugin_info.dict()
                        update_data["status"] = existing.get("status", plugin_info.status)
                        update_data["allowed_roles"] = existing.get("allowed_roles", plugin_info.allowed_roles)
                        update_data["install_date"] = existing.get("install_date", datetime.utcnow())
                        update_data["last_updated"] = datetime.utcnow()
                        
                        await plugins_collection.update_one(
                            {"plugin_id": plugin_id},
                            {"$set": update_data}
                        )
                        logger.info(f"Updated existing plugin: {plugin_id} with status {update_data['status']}")
                        
                except Exception as e:
                    logger.error(f"Error initializing plugin {plugin_id}: {e}")
                    continue
                    
            # Count total plugins in database
            total_count = await plugins_collection.count_documents({})
            logger.info(f"Plugin registry initialized - {total_count} plugins total in database")
            
            # Synchronize plugin status with actual container status
            await self.sync_plugin_status()
            
        except Exception as e:
            logger.error(f"Error initializing plugins: {e}")
            raise PluginError("system", "initialize", PluginErrorCode.CONFIGURATION_ERROR, str(e))

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
            
            for container in containers:
                # Check if container name contains the service name
                if service_name in container.name or any(service_name in label for label in container.labels.values()):
                    return container.status
                    
            # If no exact match, try finding by compose service label
            containers_with_labels = docker_client.containers.list(
                all=True, 
                filters={"label": f"com.docker.compose.service={service_name}"}            )
            
            if containers_with_labels:
                return containers_with_labels[0].status
                
            return "not_found"
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return None
    
    async def start_plugin(self, plugin_id: str) -> PluginStatusResponse:
        """Start a plugin using Docker Compose"""
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
                import subprocess
                import os
                import asyncio
                
                # Use the copied project directory
                project_dir = "/project"
                if not os.path.exists(project_dir):
                    project_dir = "/app"  # Fallback
                
                service_name = plugin.docker_service_name
                
                logger.info(f"Starting plugin {plugin_id} with service {service_name}")
                
                # Build the service first (in case it's not built)
                build_cmd = ["docker", "compose", "-f", f"{project_dir}/docker-compose.yml", "build", service_name]
                build_result = subprocess.run(
                    build_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout for building
                    cwd=project_dir
                )
                
                if build_result.returncode != 0:
                    logger.warning(f"Build failed for {service_name}: {build_result.stderr}")
                    # Continue anyway, maybe it's already built
                
                # Start the service
                start_cmd = ["docker", "compose", "-f", f"{project_dir}/docker-compose.yml", "up", "-d", service_name]
                start_result = subprocess.run(
                    start_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout for starting
                    cwd=project_dir
                )
                
                if start_result.returncode == 0:
                    logger.info(f"Successfully started {service_name}")
                    
                    # Wait for container to be ready
                    await asyncio.sleep(5)
                    
                    # Verify the container is running
                    docker_client = self.get_docker_client()
                    if docker_client:
                        # Try to find the container
                        containers = docker_client.containers.list(filters={"label": f"com.docker.compose.service={service_name}"})
                        if containers and containers[0].status == "running":
                            await self.update_plugin_status(plugin_id, PluginStatus.ACTIVE)
                            return PluginStatusResponse(
                                plugin_id=plugin_id,
                                status=PluginStatus.ACTIVE,
                                message="Plugin started successfully",
                                container_status="running"
                            )
                    
                    # Even if we can't verify, the compose command succeeded
                    await self.update_plugin_status(plugin_id, PluginStatus.ACTIVE)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.ACTIVE,
                        message="Plugin started via Docker Compose",
                        container_status="started"
                    )
                else:
                    error_msg = start_result.stderr or start_result.stdout or "Unknown error"
                    logger.error(f"Failed to start {service_name}: {error_msg}")
                    await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.ERROR,
                        message=f"Failed to start plugin: {error_msg}",
                        container_status="start_failed"
                    )
                    
            except subprocess.TimeoutExpired:
                await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message="Timeout starting plugin",
                    container_status="timeout"
                )
            except Exception as docker_error:
                logger.error(f"Error in start_plugin: {docker_error}")
                await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message=f"Error starting plugin: {str(docker_error)}",
                    container_status="error"
                )                
        except Exception as e:
            logger.error(f"Error starting plugin {plugin_id}: {e}")
            await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
            return PluginStatusResponse(
                plugin_id=plugin_id,
                status=PluginStatus.ERROR,
                message=f"Error starting plugin: {str(e)}"
            )
    
    async def stop_plugin(self, plugin_id: str) -> PluginStatusResponse:
        """Stop a plugin using Docker Compose"""
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
            
            try:
                import subprocess
                import os
                import asyncio
                
                # Use the copied project directory
                project_dir = "/project"
                if not os.path.exists(project_dir):
                    project_dir = "/app"  # Fallback
                
                service_name = plugin.docker_service_name
                
                logger.info(f"Stopping plugin {plugin_id} with service {service_name}")
                
                # Stop the service
                stop_cmd = ["docker", "compose", "-f", f"{project_dir}/docker-compose.yml", "stop", service_name]
                stop_result = subprocess.run(
                    stop_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,  # 1 minute timeout for stopping
                    cwd=project_dir
                )
                
                if stop_result.returncode == 0:
                    logger.info(f"Successfully stopped {service_name}")
                    
                    # Wait for container to stop
                    await asyncio.sleep(3)
                    
                    await self.update_plugin_status(plugin_id, PluginStatus.INACTIVE)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.INACTIVE,
                        message="Plugin stopped successfully",
                        container_status="stopped"
                    )
                else:
                    error_msg = stop_result.stderr or stop_result.stdout or "Unknown error"
                    logger.error(f"Failed to stop {service_name}: {error_msg}")
                    await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                    return PluginStatusResponse(
                        plugin_id=plugin_id,
                        status=PluginStatus.ERROR,
                        message=f"Failed to stop plugin: {error_msg}",
                        container_status="stop_failed"
                    )
                    
            except subprocess.TimeoutExpired:
                await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message="Timeout stopping plugin",
                    container_status="timeout"
                )
            except Exception as docker_error:
                logger.error(f"Error in stop_plugin: {docker_error}")
                await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
                return PluginStatusResponse(
                    plugin_id=plugin_id,
                    status=PluginStatus.ERROR,
                    message=f"Error stopping plugin: {str(docker_error)}",
                    container_status="error"
                )                
        except Exception as e:
            logger.error(f"Error stopping plugin {plugin_id}: {e}")
            await self.update_plugin_status(plugin_id, PluginStatus.ERROR)
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
            logger.info(f"Searching for container with service name: {service_name}")
            
            # Strategy 1: Find by Docker Compose service label
            containers = docker_client.containers.list(
                all=True, 
                filters={"label": f"com.docker.compose.service={service_name}"}
            )
            
            logger.info(f"Strategy 1 - Found {len(containers)} containers with compose service label")
            if containers:
                logger.info(f"Found container via strategy 1: {containers[0].name}")
                return containers[0]
            
            # Strategy 2: Find by container name containing service name
            all_containers = docker_client.containers.list(all=True)
            logger.info(f"Strategy 2 - Checking {len(all_containers)} total containers")
            logger.info(f"Available containers: {[c.name for c in all_containers]}")
            
            for container in all_containers:
                if service_name in container.name:
                    logger.info(f"Found container via strategy 2: {container.name}")
                    return container
            
            # Strategy 3: Find by project and service (for newer Docker Compose)
            project_containers = docker_client.containers.list(
                all=True,
                filters={"label": "com.docker.compose.project=samfms"}
            )
            
            logger.info(f"Strategy 3 - Found {len(project_containers)} containers with project label")
            for container in project_containers:
                labels = container.labels
                logger.info(f"Container {container.name} labels: {labels}")
                if labels.get("com.docker.compose.service") == service_name:
                    logger.info(f"Found container via strategy 3: {container.name}")
                    return container
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding container for service {service_name}: {e}")
            return None
    
    async def check_plugin_health(self, plugin: PluginInfo) -> bool:
        """Check if a plugin service is healthy by testing its health endpoint"""
        import urllib.request
        import urllib.error
        
        if not plugin.port or not plugin.health_endpoint:
            logger.debug(f"Plugin {plugin.plugin_id} has no health endpoint configured")
            return False
            
        health_url = f"http://localhost:{plugin.port}{plugin.health_endpoint}"
        
        try:
            request = urllib.request.Request(health_url)
            request.add_header('User-Agent', 'SAMFMS-Plugin-Manager/1.0')
            
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status == 200
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
