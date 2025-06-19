"""
Request Router Service for SAMFMS Core
Handles routing requests to appropriate service blocks via RabbitMQ with resilience patterns
"""

import asyncio
import uuid
import time
import fnmatch
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import httpx
from fastapi import HTTPException, status

from rabbitmq.producer import publish_message
from rabbitmq.admin import create_exchange
import aio_pika
from services.resilience import resilience_manager, request_tracer

logger = logging.getLogger(__name__)

class RequestRouter:
    """Routes requests to appropriate service blocks and manages responses"""
    
    def __init__(self):
        self.response_manager = ResponseCorrelationManager()
        self.routing_map = {
            "/api/vehicles/*": "management",
            "/api/vehicle-assignments/*": "management",
            "/api/vehicle-usage/*": "management",
            "/api/gps/*": "gps",
            "/api/tracking/*": "gps", 
            "/api/trips/*": "trip_planning",
            "/api/trip-planning/*": "trip_planning",
            "/api/maintenance/*": "maintenance",
            "/api/vehicle-maintenance/*": "maintenance"        }
    
    async def initialize(self):
        """Initialize routing infrastructure"""
        try:
            # Create request/response exchanges
            await create_exchange("service_requests", aio_pika.ExchangeType.DIRECT)
            await create_exchange("service_responses", aio_pika.ExchangeType.DIRECT)
            
            # Start response consumer
            asyncio.create_task(self.response_manager.consume_responses())
            
            logger.info("Request router initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize request router: {e}")
            raise
    
    def get_service_for_endpoint(self, endpoint: str) -> str:
        """Determine target service based on endpoint pattern"""
        for pattern, service in self.routing_map.items():
            if fnmatch.fnmatch(endpoint, pattern):
                return service
        raise ValueError(f"No service found for endpoint: {endpoint}")
    
    async def route_request(self, endpoint: str, method: str, data: Dict[Any, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate service and wait for response with resilience"""
        try:
            # Determine target service
            service = self.get_service_for_endpoint(endpoint)
            
            # Create correlation ID for tracking
            correlation_id = str(uuid.uuid4())
            
            # Create trace context
            trace_context = request_tracer.create_trace_context(
                correlation_id, user_context.get("user_id", "unknown")
            )
            
            # Prepare request message
            request_msg = {
                "correlation_id": correlation_id,
                "endpoint": endpoint,
                "method": method,
                "data": data,
                "user_context": user_context,
                "timestamp": datetime.utcnow().isoformat(),
                "service": service,
                "trace_id": correlation_id
            }
            
            logger.info(f"Routing request {correlation_id} to service {service} for endpoint {endpoint}")
            
            # Send request with resilience patterns
            start_time = time.time()
            try:
                response = await resilience_manager.call_service_with_resilience(
                    service,
                    lambda: self.send_request_and_wait(service, request_msg, correlation_id),
                    retry_config={
                        "max_retries": 2,  # Reduced retries for user-facing requests
                        "base_delay": 0.5,
                        "max_delay": 10.0
                    }
                )
                
                # Log successful service call
                duration = time.time() - start_time
                request_tracer.log_service_call(
                    correlation_id, service, f"{method} {endpoint}", duration, "success"
                )
                
                # Complete trace
                request_tracer.complete_trace(correlation_id, "success")
                
                return response
                
            except Exception as e:
                # Log failed service call
                duration = time.time() - start_time
                request_tracer.log_service_call(
                    correlation_id, service, f"{method} {endpoint}", duration, "error", str(e)
                )
                
                # Complete trace with error
                request_tracer.complete_trace(correlation_id, "error")
                raise
            
        except ValueError as e:
            logger.error(f"Routing error: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Request routing failed: {e}")
            raise HTTPException(status_code=500, detail="Internal service error")
    
    async def send_request_and_wait(self, service: str, request_msg: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Send request via RabbitMQ and wait for response"""
        try:
            # Register for response
            response_future = self.response_manager.register_pending_request(correlation_id)
            
            # Send request to service queue
            routing_key = f"{service}.requests"
            await publish_message(
                "service_requests",
                aio_pika.ExchangeType.DIRECT,
                request_msg,
                routing_key=routing_key
            )
            
            # Wait for response with timeout
            response = await self.response_manager.wait_for_response(correlation_id, timeout=30)
            
            if response.get("status") == "error":
                error_msg = response.get("error", "Service error")
                raise HTTPException(status_code=500, detail=error_msg)
            
            return response.get("data", {})
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from {service} for correlation_id {correlation_id}")
            raise HTTPException(status_code=504, detail=f"Service {service} timeout")
        except Exception as e:
            logger.error(f"Error sending request to {service}: {e}")
            raise

class ResponseCorrelationManager:
    """Manages correlation between requests and responses"""
    
    def __init__(self):
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.response_futures: Dict[str, asyncio.Future] = {}
        
    def register_pending_request(self, correlation_id: str) -> asyncio.Future:
        """Register a pending request and return future for response"""
        future = asyncio.Future()
        self.response_futures[correlation_id] = future
        return future
    
    async def wait_for_response(self, correlation_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for response with timeout"""
        future = self.response_futures.get(correlation_id)
        if not future:
            raise ValueError(f"No pending request found for correlation_id: {correlation_id}")
        
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.error(f"Response timeout for correlation_id: {correlation_id}")
            raise
        finally:
            # Clean up
            self.response_futures.pop(correlation_id, None)
    
    async def handle_response(self, response: Dict[str, Any]):
        """Handle incoming response and resolve corresponding future"""
        correlation_id = response.get("correlation_id")
        if not correlation_id:
            logger.warning("Received response without correlation_id")
            return
        
        future = self.response_futures.get(correlation_id)
        if future and not future.done():
            future.set_result(response)
            logger.debug(f"Response handled for correlation_id: {correlation_id}")
        else:
            logger.warning(f"No pending future found for correlation_id: {correlation_id}")
    
    async def consume_responses(self):
        """Consume responses from service response queue"""
        try:
            from rabbitmq.consumer import consume_messages_with_handler
            await consume_messages_with_handler("core.responses", self.handle_response)
        except Exception as e:
            logger.error(f"Error consuming responses: {e}")


# Global instance
request_router = RequestRouter()
