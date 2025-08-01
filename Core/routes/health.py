"""
Health Check Routes
Provides comprehensive health status for all system components
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import asyncio
import logging
from datetime import datetime

from services.circuit_breaker import circuit_breaker_manager
from services.request_deduplicator import request_deduplicator
from services.distributed_tracer import distributed_tracer

logger = logging.getLogger(__name__)

health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "samfms-core"
    }

@health_router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Comprehensive health check with all dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "samfms-core",
        "version": "1.0.0",
        "checks": {}
    }
    
    overall_healthy = True
    
    # Check database health
    try:
        from database import get_database_manager
        db_manager = await get_database_manager()
        db_health = await db_manager.health_check()
        health_status["checks"]["database"] = db_health
        if db_health.get("status") != "healthy":
            overall_healthy = False
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check RabbitMQ health
    try:
        import aio_pika
        from rabbitmq.admin import RABBITMQ_URL
        
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        await connection.close()
        health_status["checks"]["rabbitmq"] = {
            "status": "healthy",
            "url": RABBITMQ_URL.split('@')[1] if '@' in RABBITMQ_URL else "hidden"
        }
    except Exception as e:
        health_status["checks"]["rabbitmq"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check service discovery
    try:
        from common.service_discovery import get_service_discovery
        service_discovery = await get_service_discovery()
        services = await service_discovery.get_healthy_services()
        health_status["checks"]["service_discovery"] = {
            "status": "healthy",
            "registered_services": len(services),
            "services": [s.get("name", "unknown") for s in services[:5]]  # Show first 5
        }
    except Exception as e:
        health_status["checks"]["service_discovery"] = {
            "status": "degraded",
            "error": str(e)
        }
        # Service discovery failure is not critical
    
    # Check circuit breakers
    try:
        circuit_states = circuit_breaker_manager.get_all_states()
        healthy_circuits = sum(1 for state in circuit_states.values() if state["state"] == "closed")
        total_circuits = len(circuit_states)
        
        health_status["checks"]["circuit_breakers"] = {
            "status": "healthy" if healthy_circuits == total_circuits else "degraded",
            "healthy_circuits": healthy_circuits,
            "total_circuits": total_circuits,
            "states": circuit_states
        }
        
        if healthy_circuits < total_circuits:
            overall_healthy = False
    except Exception as e:
        health_status["checks"]["circuit_breakers"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Check request deduplicator
    try:
        dedup_stats = request_deduplicator.get_stats()
        health_status["checks"]["request_deduplicator"] = {
            "status": "healthy",
            "stats": dedup_stats
        }
    except Exception as e:
        health_status["checks"]["request_deduplicator"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    # Return appropriate HTTP status
    status_code = 200 if overall_healthy else 503
    return JSONResponse(content=health_status, status_code=status_code)

@health_router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check - is the service ready to handle requests"""
    ready_status = {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    overall_ready = True
    
    # Check if response manager is ready
    try:
        from services.request_router import request_router
        await asyncio.wait_for(request_router.response_manager.wait_for_ready(), timeout=1.0)
        ready_status["checks"]["response_manager"] = {"status": "ready"}
    except Exception as e:
        ready_status["checks"]["response_manager"] = {
            "status": "not_ready",
            "error": str(e)
        }
        overall_ready = False
    
    # Check basic database connectivity
    try:
        from database import get_database_manager
        db_manager = await get_database_manager()
        if hasattr(db_manager, 'client') and db_manager.client:
            ready_status["checks"]["database"] = {"status": "ready"}
        else:
            ready_status["checks"]["database"] = {"status": "not_ready", "reason": "not_connected"}
            overall_ready = False
    except Exception as e:
        ready_status["checks"]["database"] = {
            "status": "not_ready",
            "error": str(e)
        }
        overall_ready = False
    
    ready_status["status"] = "ready" if overall_ready else "not_ready"
    status_code = 200 if overall_ready else 503
    
    return JSONResponse(content=ready_status, status_code=status_code)

@health_router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check - is the service alive"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "samfms-core"
    }

@health_router.get("/circuit-breakers")
async def circuit_breaker_status() -> Dict[str, Any]:
    """Get detailed circuit breaker status"""
    try:
        states = circuit_breaker_manager.get_all_states()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "circuit_breakers": states
        }
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get circuit breaker status")

@health_router.get("/metrics")
async def system_metrics() -> Dict[str, Any]:
    """Get system metrics and statistics"""
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "deduplicator": request_deduplicator.get_stats(),
            "circuit_breakers": circuit_breaker_manager.get_all_states(),
            "tracing": distributed_tracer.get_trace_stats()
        }
        
        # Add memory usage if available
        try:
            import psutil
            process = psutil.Process()
            metrics["memory"] = {
                "rss_mb": process.memory_info().rss / 1024 / 1024,
                "vms_mb": process.memory_info().vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            metrics["memory"] = {"status": "psutil_not_available"}
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@health_router.get("/traces")
async def get_recent_traces(limit: int = 50) -> Dict[str, Any]:
    """Get recent request traces"""
    try:
        traces = distributed_tracer.get_recent_traces(limit)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "traces": traces,
            "count": len(traces)
        }
    except Exception as e:
        logger.error(f"Error getting traces: {e}")
        raise HTTPException(status_code=500, detail="Failed to get traces")

@health_router.get("/traces/{correlation_id}")
async def get_trace_details(correlation_id: str) -> Dict[str, Any]:
    """Get detailed trace information for a specific correlation ID"""
    try:
        trace = distributed_tracer.get_trace_summary(correlation_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "trace": trace
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trace details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trace details")
 
# Get healthy services/sblocks for display on frontend   
from .service_routing import route_to_service_block

@health_router.get("/healthy-services")
async def get_healthy_services() -> Dict[str, Any]:
    sblocks = ["management", "maintenance", "gps", "trips"]
    results = {}
    for block in sblocks:
        try:
            resp = await route_to_service_block(service_name=block, method="GET", path="health", headers={}, body=None, query_params=None)
            results[block] = resp.get("data", {})
        except Exception as e:
            logger.warning(f"{block} health check failed: {e}")
            results[block] = {"status": "unavailable", "error": str(e)}
    return {"timestamp": datetime.utcnow().isoformat(), "sblocks": results}
            
