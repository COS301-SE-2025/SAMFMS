"""
Plugin management routes for SAMFMS Core service
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List, Dict, Dict
import logging

from models.plugin_models import PluginInfo, PluginUpdateRequest, PluginStatusResponse
from services.plugin_service import plugin_manager
from auth_service import verify_token, get_current_user_from_token
from rabbitmq.admin import addSblock, removeSblock

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/plugins", tags=["Plugin Management"])
security = HTTPBearer()

@router.get("/", response_model=List[PluginInfo])
async def get_all_plugins(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all available plugins - admin only"""
    try:
        # Verify user is admin
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view plugins"
            )
        
        plugins = await plugin_manager.get_all_plugins()
        return plugins
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plugins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving plugins: {str(e)}"
        )

@router.get("/available", response_model=List[PluginInfo])
async def get_available_plugins(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get plugins available to current user based on their role"""
    try:
        user_info = verify_token(credentials)
        user_role = user_info.get("role")
        
        all_plugins = await plugin_manager.get_all_plugins()
        
        # Filter plugins based on user role and active status
        available_plugins = [
            plugin for plugin in all_plugins
            if plugin_manager.user_has_plugin_access(user_role, plugin)
            and plugin.status == "active"
        ]
        
        return available_plugins
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available plugins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving available plugins: {str(e)}"
        )

@router.get("/{plugin_id}", response_model=PluginInfo)
async def get_plugin(
    plugin_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get specific plugin information"""
    try:
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view plugin details"
            )
        
        plugin = await plugin_manager.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plugin not found"
            )
        
        return plugin
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plugin {plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving plugin: {str(e)}"
        )

@router.post("/{plugin_id}/start", response_model=PluginStatusResponse)
async def start_plugin(
    plugin_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Start a plugin (activate container)"""
    try:
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can start plugins"
            )
        
        result = await plugin_manager.start_plugin(plugin_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting plugin {plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting plugin: {str(e)}"
        )

@router.post("/{plugin_id}/stop", response_model=PluginStatusResponse)
async def stop_plugin(
    plugin_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Stop a plugin (deactivate container)"""
    try:
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can stop plugins"
            )
        
        result = await plugin_manager.stop_plugin(plugin_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping plugin {plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping plugin: {str(e)}"
        )

@router.put("/{plugin_id}/roles")
async def update_plugin_roles(
    plugin_id: str,
    update_request: PluginUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update plugin role permissions"""
    try:
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update plugin roles"
            )
        
        if not update_request.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="allowed_roles is required"
            )
        
        # Verify plugin exists
        plugin = await plugin_manager.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plugin not found"
            )
        
        # Update roles
        success = await plugin_manager.update_plugin_roles(plugin_id, update_request.allowed_roles)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update plugin roles"
            )
        
        return {"message": f"Plugin {plugin_id} roles updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating plugin roles {plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating plugin roles: {str(e)}"
        )

# Add route for getting runtime plugin status
@router.get("/{plugin_id}/status", response_model=Dict[str, str])
async def get_plugin_runtime_status(
    plugin_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get comprehensive runtime status of a plugin"""
    try:
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view plugin runtime status"
            )
        
        status_info = await plugin_manager.get_plugin_runtime_status(plugin_id)
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plugin runtime status {plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving plugin runtime status: {str(e)}"
        )

@router.post("/sync-status")
async def sync_plugin_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Synchronize plugin status with actual container status - admin only"""
    try:
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can sync plugin status"
            )
        
        await plugin_manager.sync_plugin_status()
        return {"message": "Plugin status synchronized successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing plugin status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing plugin status: {str(e)}"
        )

@router.get("/debug/docker")
async def debug_docker_access(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Debug endpoint to test Docker access"""
    try:
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can access debug endpoints"
            )
        
        import os
        import docker
        
        debug_info = {
            "docker_socket_exists": os.path.exists("/var/run/docker.sock"),
            "docker_socket_permissions": None,
            "current_user": os.getuid() if hasattr(os, 'getuid') else 'unknown',
            "current_groups": os.getgroups() if hasattr(os, 'getgroups') else 'unknown',
            "docker_client_status": "unknown",
            "docker_version": None,
            "containers": [],
            "error": None
        }
        
        # Check socket permissions
        if debug_info["docker_socket_exists"]:
            try:
                stat_info = os.stat("/var/run/docker.sock")
                debug_info["docker_socket_permissions"] = {
                    "mode": oct(stat_info.st_mode),
                    "owner": stat_info.st_uid,
                    "group": stat_info.st_gid
                }
            except Exception as e:
                debug_info["socket_stat_error"] = str(e)
        
        # Test Docker client
        try:
            client = docker.from_env()
            debug_info["docker_client_status"] = "initialized"
            
            # Test ping
            client.ping()
            debug_info["docker_client_status"] = "ping_successful"
            
            # Get version
            version_info = client.version()
            debug_info["docker_version"] = version_info.get('Version', 'unknown')
            
            # List containers
            containers = client.containers.list(all=True, limit=5)
            debug_info["containers"] = [
                {
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags[0] if c.image.tags else "unknown"
                } for c in containers
            ]
            
        except Exception as e:
            debug_info["error"] = str(e)
            debug_info["docker_client_status"] = "failed"
        
        return debug_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Docker debug: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug error: {str(e)}"
        )


@router.get("/sblock/add/{username}", tags=["SBlock"])
async def add_sblock(username: str):
    try:
        credentials: HTTPAuthorizationCredentials = Depends(security)
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view plugins"
            )
        
        await addSblock(username)
        return {"status": "success", "message": f"SBlock {username} added"}
    except Exception as e:
        logger.error(f"Error adding SBlock: {str(e)}")
        return {"status": "error", "message": str(e)}
    

    
@router.get("/sblock/remove/{username}", tags=["SBlock"])
async def remove_sblock(username: str):
    try:
        credentials: HTTPAuthorizationCredentials = Depends(security)
        user_info = verify_token(credentials)
        if user_info.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can view plugins"
            )
        
        await removeSblock(username)
        return {"status": "success", "message": f"SBlock {username} removed"}
    

    except Exception as e:
        logger.error(f"Error removing SBlock: {str(e)}")
        return {"status": "error", "message": str(e)}
    