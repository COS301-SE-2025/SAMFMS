"""
Health check and metrics module for GPS Service.
Provides comprehensive health monitoring and performance metrics.
"""

import time
import psutil
import os
from datetime import datetime
from typing import Dict, Any
from connections import ConnectionManager
from logging_config import get_logger

logger = get_logger(__name__)

# Service metadata
SERVICE_NAME = "gps-service"
SERVICE_VERSION = "1.0.0"
START_TIME = time.time()


class HealthChecker:
    """Provides health check functionality for the service and its dependencies."""
    
    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        """
        Perform comprehensive health check of the service and dependencies.
        
        Returns:
            Dictionary containing health status information
        """
        start_time = time.time()
        
        health_status = {
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": {},
            "uptime_seconds": round(time.time() - START_TIME, 2)
        }
        
        # Check Redis
        redis_healthy = ConnectionManager.test_redis_connection()
        health_status["checks"]["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "message": "Connection successful" if redis_healthy else "Connection failed"
        }
        
        if not redis_healthy:
            health_status["status"] = "degraded"
        
        # Check RabbitMQ
        rabbitmq_healthy = ConnectionManager.test_rabbitmq_connection()
        health_status["checks"]["rabbitmq"] = {
            "status": "healthy" if rabbitmq_healthy else "unhealthy",
            "message": "Connection successful" if rabbitmq_healthy else "Connection failed"
        }
        
        if not rabbitmq_healthy:
            health_status["status"] = "degraded"
        
        # Check disk space
        disk_status = HealthChecker._check_disk_space()
        health_status["checks"]["disk"] = disk_status
        if disk_status["status"] != "healthy":
            health_status["status"] = "degraded"
        
        # Check memory usage
        memory_status = HealthChecker._check_memory_usage()
        health_status["checks"]["memory"] = memory_status
        if memory_status["status"] != "healthy":
            health_status["status"] = "degraded"
        
        # Calculate response time
        duration_ms = round((time.time() - start_time) * 1000, 2)
        health_status["response_time_ms"] = duration_ms
        
        # Log health check result
        logger.info(
            "Health check completed",
            extra={
                "status": health_status["status"],
                "duration_ms": duration_ms,
                "redis_status": health_status["checks"]["redis"]["status"],
                "rabbitmq_status": health_status["checks"]["rabbitmq"]["status"],
                "disk_status": health_status["checks"]["disk"]["status"],
                "memory_status": health_status["checks"]["memory"]["status"]
            }
        )
        
        return health_status
    
    @staticmethod
    def _check_disk_space() -> Dict[str, Any]:
        """
        Check available disk space.
        
        Returns:
            Dictionary with disk space status
        """
        try:
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            if free_percent < 10:
                status = "unhealthy"
                message = f"Low disk space: {free_percent:.1f}% free"
            elif free_percent < 20:
                status = "warning"
                message = f"Disk space getting low: {free_percent:.1f}% free"
            else:
                status = "healthy"
                message = f"Sufficient disk space: {free_percent:.1f}% free"
            
            return {
                "status": status,
                "message": message,
                "free_percent": round(free_percent, 1),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "total_gb": round(disk_usage.total / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to check disk space: {e}")
            return {
                "status": "unknown",
                "message": f"Failed to check disk space: {str(e)}"
            }
    
    @staticmethod
    def _check_memory_usage() -> Dict[str, Any]:
        """
        Check memory usage.
        
        Returns:
            Dictionary with memory usage status
        """
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            if used_percent > 90:
                status = "unhealthy"
                message = f"High memory usage: {used_percent:.1f}%"
            elif used_percent > 80:
                status = "warning"
                message = f"Memory usage getting high: {used_percent:.1f}%"
            else:
                status = "healthy"
                message = f"Normal memory usage: {used_percent:.1f}%"
            
            return {
                "status": status,
                "message": message,
                "used_percent": round(used_percent, 1),
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to check memory usage: {e}")
            return {
                "status": "unknown",
                "message": f"Failed to check memory usage: {str(e)}"
            }


class MetricsCollector:
    """Collects and provides performance metrics for the service."""
    
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """
        Collect comprehensive performance metrics.
        
        Returns:
            Dictionary containing service metrics
        """
        try:
            # Get process information
            process = psutil.Process(os.getpid())
            
            # Connection status
            redis_conn = ConnectionManager.get_redis_connection()
            rabbitmq_conn = ConnectionManager.get_rabbitmq_connection()
            
            metrics = {
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "uptime_seconds": round(time.time() - START_TIME, 2),
                
                # System metrics
                "system": {
                    "cpu_percent": round(psutil.cpu_percent(), 2),
                    "memory_percent": round(psutil.virtual_memory().percent, 2),
                    "disk_percent": round(psutil.disk_usage('/').percent, 2),
                    "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
                },
                
                # Process metrics
                "process": {
                    "cpu_percent": round(process.cpu_percent(), 2),
                    "memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
                    "memory_percent": round(process.memory_percent(), 2),
                    "num_threads": process.num_threads(),
                    "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None,
                    "create_time": process.create_time()
                },
                
                # Connection metrics
                "connections": {
                    "redis": {
                        "status": "connected" if redis_conn else "disconnected",
                        "pool_size": len(redis_conn.connection_pool._available_connections) if redis_conn else 0
                    },
                    "rabbitmq": {
                        "status": "connected" if rabbitmq_conn and not rabbitmq_conn.is_closed else "disconnected",
                        "is_open": rabbitmq_conn.is_open if rabbitmq_conn else False
                    }
                },
                
                # Application metrics (can be extended)
                "application": {
                    "requests_total": 0,  # Would track actual request count
                    "errors_total": 0,    # Would track actual error count
                    "avg_response_time_ms": 0  # Would calculate actual average
                }
            }
            
            # Close test connection if opened
            if rabbitmq_conn and not rabbitmq_conn.is_closed:
                rabbitmq_conn.close()
            
            logger.debug("Metrics collected successfully", extra={"metrics_summary": {
                "cpu_percent": metrics["system"]["cpu_percent"],
                "memory_percent": metrics["process"]["memory_percent"],
                "uptime_seconds": metrics["uptime_seconds"]
            }})
            
            return metrics
            
        except Exception as e:
            logger.error(
                "Failed to collect metrics",
                extra={
                    "error": str(e),
                    "traceback": str(e.__traceback__)
                }
            )
            
            # Return minimal metrics on error
            return {
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "uptime_seconds": round(time.time() - START_TIME, 2),
                "error": "Failed to collect full metrics",
                "error_message": str(e)
            }


# Convenience functions
def get_health_status():
    """Get health status - convenience function."""
    return HealthChecker.get_health_status()


def get_metrics():
    """Get metrics - convenience function."""
    return MetricsCollector.get_metrics()
