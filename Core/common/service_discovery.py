"""
Service Discovery Module for SAMFMS Core
Provides service registration, discovery, and health checking capabilities
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import aiohttp
import logging
from enum import Enum

from common.exceptions import ServiceDiscoveryError, ServiceNotFoundError, HealthCheckError

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"

@dataclass
class ServiceInfo:
    """Service information data class"""
    name: str
    version: str
    host: str
    port: int
    protocol: str = "http"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: Dict[str, Any] = None
    last_heartbeat: Optional[datetime] = None
    health_check_url: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.utcnow()
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the service"""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        """Check if service is considered healthy"""
        if self.status != ServiceStatus.HEALTHY:
            return False
        
        # Check if heartbeat is recent (within 30 seconds)
        if self.last_heartbeat:
            time_diff = datetime.utcnow() - self.last_heartbeat
            return time_diff < timedelta(seconds=30)
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['last_heartbeat'] = self.last_heartbeat.isoformat() if self.last_heartbeat else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInfo':
        """Create ServiceInfo from dictionary"""
        # Convert status back to enum
        if 'status' in data:
            data['status'] = ServiceStatus(data['status'])
        
        # Convert last_heartbeat back to datetime
        if data.get('last_heartbeat'):
            data['last_heartbeat'] = datetime.fromisoformat(data['last_heartbeat'])
        
        return cls(**data)

class ServiceRegistry:
    """In-memory service registry"""
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, service: ServiceInfo) -> None:
        """Register a service"""
        async with self._lock:
            self._services[service.name] = service
            logger.info(f"🔧 Registered service: {service.name} at {service.base_url}")
    
    async def deregister(self, service_name: str) -> None:
        """Deregister a service"""
        async with self._lock:
            if service_name in self._services:
                del self._services[service_name]
                logger.info(f"🔧 Deregistered service: {service_name}")
    
    async def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get service by name"""
        async with self._lock:
            return self._services.get(service_name)
    
    async def get_services_by_tag(self, tag: str) -> List[ServiceInfo]:
        """Get services by tag"""
        async with self._lock:
            return [
                service for service in self._services.values()
                if tag in service.tags
            ]
    
    async def get_healthy_services(self) -> List[ServiceInfo]:
        """Get all healthy services"""
        async with self._lock:
            return [
                service for service in self._services.values()
                if service.is_healthy
            ]
    
    async def list_services(self) -> List[ServiceInfo]:
        """List all services"""
        async with self._lock:
            return list(self._services.values())
    
    async def update_heartbeat(self, service_name: str) -> None:
        """Update service heartbeat"""
        async with self._lock:
            if service_name in self._services:
                self._services[service_name].last_heartbeat = datetime.utcnow()
    
    async def update_status(self, service_name: str, status: ServiceStatus) -> None:
        """Update service status"""
        async with self._lock:
            if service_name in self._services:
                self._services[service_name].status = status
                logger.debug(f"Updated service {service_name} status to {status.value}")

class HealthChecker:
    """Health checker for services"""
    
    def __init__(self, registry: ServiceRegistry, check_interval: int = 10):
        self.registry = registry
        self.check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start health checking"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info(f"🔧 Health checker started with {self.check_interval}s interval")
    
    async def stop(self) -> None:
        """Stop health checking"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("🔧 Health checker stopped")
    
    async def _health_check_loop(self) -> None:
        """Main health check loop"""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_services(self) -> None:
        """Check health of all services"""
        services = await self.registry.list_services()
        
        # Create tasks for all health checks
        tasks = []
        for service in services:
            if service.health_check_url:
                task = asyncio.create_task(self._check_service_health(service))
                tasks.append(task)
        
        # Wait for all health checks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_service_health(self, service: ServiceInfo) -> None:
        """Check health of a specific service"""
        try:
            if not service.health_check_url:
                # No health check URL, assume healthy if recent heartbeat
                if service.last_heartbeat:
                    time_diff = datetime.utcnow() - service.last_heartbeat
                    if time_diff > timedelta(seconds=30):
                        await self.registry.update_status(service.name, ServiceStatus.UNHEALTHY)
                return
            
            # Perform HTTP health check
            health_url = f"{service.base_url}{service.health_check_url}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(health_url) as response:
                    if response.status == 200:
                        await self.registry.update_status(service.name, ServiceStatus.HEALTHY)
                        await self.registry.update_heartbeat(service.name)
                    else:
                        await self.registry.update_status(service.name, ServiceStatus.UNHEALTHY)
                        logger.warning(f"Service {service.name} health check failed: HTTP {response.status}")
        
        except asyncio.TimeoutError:
            await self.registry.update_status(service.name, ServiceStatus.UNHEALTHY)
            logger.warning(f"Service {service.name} health check timed out")
        
        except Exception as e:
            await self.registry.update_status(service.name, ServiceStatus.UNHEALTHY)
            logger.warning(f"Service {service.name} health check failed: {e}")

class ServiceClient:
    """HTTP client for making service-to-service calls"""
    
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def call_service(
        self,
        service_name: str,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 30
    ) -> Any:
        """
        Make a call to another service
        
        Args:
            service_name: Name of the service to call
            method: HTTP method (GET, POST, etc.)
            path: API path
            data: Request body data
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds
        
        Returns:
            Response data
        
        Raises:
            ServiceNotFoundError: If service is not found or unhealthy
            ServiceDiscoveryError: If there's an error making the call
        """
        
        service = await self.registry.get_service(service_name)
        if not service:
            raise ServiceNotFoundError(f"Service '{service_name}' not found")
        
        if not service.is_healthy:
            raise ServiceNotFoundError(f"Service '{service_name}' is not healthy")
        
        url = f"{service.base_url}{path}"
        
        try:
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            request_timeout = aiohttp.ClientTimeout(total=timeout)
            
            async with self._session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=request_timeout
            ) as response:
                
                if response.status >= 400:
                    error_text = await response.text()
                    raise ServiceDiscoveryError(
                        f"Service call failed: {response.status} {error_text}"
                    )
                
                # Try to parse JSON response
                try:
                    return await response.json()
                except aiohttp.ContentTypeError:
                    return await response.text()
        
        except asyncio.TimeoutError:
            raise ServiceDiscoveryError(f"Service call to {service_name} timed out")
        except aiohttp.ClientError as e:
            raise ServiceDiscoveryError(f"Service call to {service_name} failed: {e}")

class ServiceDiscovery:
    """Main service discovery class"""
    
    def __init__(self, health_check_interval: int = 10):
        self.registry = ServiceRegistry()
        self.health_checker = HealthChecker(self.registry, health_check_interval)
        self._started = False
    
    async def start(self) -> None:
        """Start service discovery"""
        if self._started:
            return
        
        await self.health_checker.start()
        self._started = True
        logger.info("🔧 Service discovery started")
    
    async def stop(self) -> None:
        """Stop service discovery"""
        if not self._started:
            return
        
        await self.health_checker.stop()
        self._started = False
        logger.info("🔧 Service discovery stopped")
    
    async def register_service(
        self,
        name: str,
        host: str,
        port: int,
        version: str = "1.0.0",
        protocol: str = "http",
        health_check_url: str = "/health",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> ServiceInfo:
        """Register a service"""
        
        service = ServiceInfo(
            name=name,
            version=version,
            host=host,
            port=port,
            protocol=protocol,
            status=ServiceStatus.STARTING,
            health_check_url=health_check_url,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        await self.registry.register(service)
        return service
    
    async def deregister_service(self, service_name: str) -> None:
        """Deregister a service"""
        await self.registry.deregister(service_name)
    
    async def discover_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Discover a service by name"""
        return await self.registry.get_service(service_name)
    
    async def discover_services_by_tag(self, tag: str) -> List[ServiceInfo]:
        """Discover services by tag"""
        return await self.registry.get_services_by_tag(tag)
    
    async def get_healthy_services(self) -> List[ServiceInfo]:
        """Get all healthy services"""
        return await self.registry.get_healthy_services()
    
    async def heartbeat(self, service_name: str) -> None:
        """Send heartbeat for a service"""
        await self.registry.update_heartbeat(service_name)
    
    def get_client(self) -> ServiceClient:
        """Get a service client for making calls"""
        return ServiceClient(self.registry)

# Global service discovery instance
_service_discovery: Optional[ServiceDiscovery] = None

async def get_service_discovery() -> ServiceDiscovery:
    """Get global service discovery instance"""
    global _service_discovery
    
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
        await _service_discovery.start()
    
    return _service_discovery

async def shutdown_service_discovery():
    """Shutdown global service discovery instance"""
    global _service_discovery
    
    if _service_discovery:
        await _service_discovery.stop()
        _service_discovery = None

# Convenience functions
async def register_service(
    name: str,
    host: str,
    port: int,
    **kwargs
) -> ServiceInfo:
    """Convenience function to register a service"""
    sd = await get_service_discovery()
    return await sd.register_service(name, host, port, **kwargs)

async def discover_service(service_name: str) -> Optional[ServiceInfo]:
    """Convenience function to discover a service"""
    sd = await get_service_discovery()
    return await sd.discover_service(service_name)

async def call_service(
    service_name: str,
    method: str,
    path: str,
    **kwargs
) -> Any:
    """Convenience function to call a service"""
    sd = await get_service_discovery()
    async with sd.get_client() as client:
        return await client.call_service(service_name, method, path, **kwargs)
