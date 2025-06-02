import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status, Response
from database import test_database_connection
from datetime import datetime
import os
import psutil
import time

logger = logging.getLogger(__name__)
metrics_router = APIRouter(tags=["Health Metrics"])

# Store service start time
SERVICE_START_TIME = time.time()

@metrics_router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check endpoint that can be used for kubernetes/container probes"""
    try:
        # Check database connection
        db_connection = await test_database_connection()
        
        if not db_connection:
            return Response(
                content=json.dumps({"status": "degraded", "database": "unavailable"}),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                media_type="application/json"
            )
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            content=json.dumps({"status": "unhealthy", "error": str(e)}),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json"
        )

@metrics_router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics_endpoint():
    """Endpoint providing basic service metrics"""
    try:
        # Get process metrics
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # Calculate uptime
        uptime_seconds = time.time() - SERVICE_START_TIME
        
        # Format metrics
        metrics = {
            "uptime_seconds": round(uptime_seconds),
            "memory_usage_mb": round(memory_info.rss / (1024 * 1024), 2),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "thread_count": process.num_threads(),
            "connection_count": len(process.connections()),
            "open_files": len(process.open_files()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to gather metrics: {e}")
        return Response(
            content=json.dumps({"status": "error", "message": str(e)}),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json"
        )