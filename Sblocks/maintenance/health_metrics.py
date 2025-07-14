"""
Health metrics collection for Maintenance Service
"""

import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HealthMetrics:
    """Collects and provides health metrics for the maintenance service"""
    
    def __init__(self):
        self.start_time = time.time()
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "percent": memory_percent,
                    "available_bytes": memory_available,
                    "total_bytes": memory.total
                },
                "disk": {
                    "percent": disk_percent,
                    "free_bytes": disk_free,
                    "total_bytes": disk.total
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {"error": "Failed to collect system metrics"}
            
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service-specific metrics"""
        try:
            uptime = time.time() - self.start_time
            
            return {
                "service": "maintenance",
                "uptime_seconds": uptime,
                "uptime_formatted": self._format_uptime(uptime),
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "current_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error collecting service metrics: {e}")
            return {"error": "Failed to collect service metrics"}
            
    def _format_uptime(self, uptime_seconds: float) -> str:
        """Format uptime in human-readable format"""
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)


# Global health metrics instance
health_metrics = HealthMetrics()
