"""
Plugin configuration loader and manager
"""

import yaml
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
from models.plugin_models import PluginInfo, PluginCategory, PluginStatus, PluginError, PluginErrorCode

logger = logging.getLogger(__name__)

class PluginConfigLoader:
    """Loads and manages plugin configurations"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config", "plugins.yaml")
        self._plugins_config = {}
        self._loaded = False
        
    def load_config(self) -> Dict:
        """Load plugin configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"Plugin configuration file not found: {self.config_path}")
                return {}
                
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                
            self._plugins_config = config.get('plugins', {})
            self._loaded = True
            logger.info(f"Loaded {len(self._plugins_config)} plugin configurations")
            return self._plugins_config
            
        except Exception as e:
            logger.error(f"Error loading plugin configuration: {e}")
            raise PluginError("system", "load_config", PluginErrorCode.CONFIGURATION_ERROR, str(e))
    
    def get_plugin_config(self, plugin_id: str) -> Optional[Dict]:
        """Get configuration for a specific plugin"""
        if not self._loaded:
            self.load_config()
            
        return self._plugins_config.get(plugin_id)
    
    def get_all_plugins_config(self) -> Dict:
        """Get all plugin configurations"""
        if not self._loaded:
            self.load_config()
            
        return self._plugins_config
    
    def create_plugin_info(self, plugin_id: str, config: Dict) -> PluginInfo:
        """Create a PluginInfo object from configuration"""
        try:
            return PluginInfo(
                plugin_id=plugin_id,
                name=config.get('name', plugin_id),
                description=config.get('description', ''),
                version=config.get('version', '1.0.0'),
                docker_service_name=config.get('docker_service_name', plugin_id),
                status=PluginStatus.INACTIVE,  # Default status
                allowed_roles=config.get('allowed_roles', []),
                port=config.get('port'),
                health_endpoint=config.get('health_endpoint', '/health'),
                required=config.get('required', False),
                category=PluginCategory(config.get('category', 'utilities')),
                dependencies=config.get('dependencies', []),
                config=config.get('config', {})
            )
        except Exception as e:
            logger.error(f"Error creating plugin info for {plugin_id}: {e}")
            raise PluginError(plugin_id, "create_info", PluginErrorCode.CONFIGURATION_ERROR, str(e))
    
    def validate_plugin_config(self, plugin_id: str, config: Dict) -> bool:
        """Validate plugin configuration"""
        required_fields = ['name', 'docker_service_name']
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Plugin {plugin_id} missing required field: {field}")
                return False
        
        # Validate category
        if 'category' in config:
            try:
                PluginCategory(config['category'])
            except ValueError:
                logger.error(f"Plugin {plugin_id} has invalid category: {config['category']}")
                return False
        
        # Validate port
        if 'port' in config:
            port = config['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                logger.error(f"Plugin {plugin_id} has invalid port: {port}")
                return False
        
        return True
    
    def get_plugins_by_category(self, category: PluginCategory) -> List[str]:
        """Get plugin IDs by category"""
        if not self._loaded:
            self.load_config()
            
        return [
            plugin_id for plugin_id, config in self._plugins_config.items()
            if config.get('category') == category.value
        ]
    
    def get_required_plugins(self) -> List[str]:
        """Get required plugin IDs"""
        if not self._loaded:
            self.load_config()
            
        return [
            plugin_id for plugin_id, config in self._plugins_config.items()
            if config.get('required', False)
        ]
    
    def get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """Get dependencies for a plugin"""
        config = self.get_plugin_config(plugin_id)
        if not config:
            return []
            
        return config.get('dependencies', [])
    
    def validate_dependencies(self, plugin_id: str) -> bool:
        """Validate that all dependencies are available"""
        dependencies = self.get_plugin_dependencies(plugin_id)
        
        for dep in dependencies:
            if dep not in self._plugins_config:
                logger.error(f"Plugin {plugin_id} has missing dependency: {dep}")
                return False
        
        return True

# Global instance
plugin_config_loader = PluginConfigLoader()
