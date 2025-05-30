from fastapi import HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import psutil
import redis
import logging
from database import test_database_connection
from message_queue import mq_service

logger = logging.getLogger(__name__)


async def health_check():
    """Comprehensive health check for the Security service"""
    health_status = {
        "service": "security",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "checks": {}
    }
    
    overall_healthy = True
    
    # Database connectivity check
    try:
        db_healthy = await test_database_connection()
        health_status["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "response_time_ms": 0  # Could implement actual timing
        }
        if not db_healthy:
            overall_healthy = False
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Redis connectivity check
    try:
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": 0
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # RabbitMQ connectivity check
    try:
        if mq_service.connection and mq_service.connection.is_open:
            health_status["checks"]["rabbitmq"] = {
                "status": "healthy",
                "connection": "open"
            }
        else:
            health_status["checks"]["rabbitmq"] = {
                "status": "unhealthy",
                "connection": "closed"
            }
            overall_healthy = False
    except Exception as e:
        health_status["checks"]["rabbitmq"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # System resource checks
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        health_status["checks"]["system"] = {
            "status": "healthy",
            "memory_usage_percent": memory.percent,
            "disk_usage_percent": disk.percent,
            "cpu_usage_percent": psutil.cpu_percent(interval=1)
        }
        
        # Mark as unhealthy if resources are critically low
        if memory.percent > 90 or disk.percent > 90:
            health_status["checks"]["system"]["status"] = "warning"
            
    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Set overall status
    if not overall_healthy:
        health_status["status"] = "unhealthy"
    
    return JSONResponse(
        content=health_status,
        status_code=200 if overall_healthy else 503
    )


async def metrics_endpoint():
    """Expose service metrics"""
    try:
        # Get system metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get process info
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics = {
            "service": "security",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": (datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds(),
            "system": {
                "memory_total_bytes": memory.total,
                "memory_available_bytes": memory.available,
                "memory_used_bytes": memory.used,
                "memory_usage_percent": memory.percent,
                "disk_total_bytes": disk.total,
                "disk_free_bytes": disk.free,
                "disk_used_bytes": disk.used,
                "disk_usage_percent": disk.percent,
                "cpu_usage_percent": cpu_percent
            },
            "process": {
                "memory_rss_bytes": process_memory.rss,
                "memory_vms_bytes": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
            }
        }
        
        return JSONResponse(content=metrics)
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail="Error generating metrics")