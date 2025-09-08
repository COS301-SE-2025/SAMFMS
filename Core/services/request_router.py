"""
Request Router Service for SAMFMS Core
Handles routing requests to appropriate service blocks via RabbitMQ with resilience patterns
"""

import asyncio
import uuid
import time
import fnmatch
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import httpx
from fastapi import HTTPException, status

from rabbitmq.producer import publish_message
#from rabbitmq.admin import create_exchange
import aio_pika
from services.resilience import resilience_manager, request_tracer
from services.circuit_breaker import circuit_breaker_manager, CircuitBreakerOpenError
from services.distributed_tracer import distributed_tracer

from utils.exceptions import ServiceUnavailableError, ServiceTimeoutError, AuthorizationError, ValidationError

logger = logging.getLogger(__name__)

class RequestRouter:
    """Routes requests to appropriate service blocks and manages responses"""
    
    def __init__(self):
        self.response_manager = ResponseCorrelationManager()
        self.routing_map = {
            # Management Service Routes - simplified
            "/management": "management",
            "/management/*": "management",
            
            # Maintenance Service Routes - simplified 
            "/maintenance": "maintenance",
            "/maintenance/*": "maintenance",
            
            # GPS Service Routes - simplified
            "/gps": "gps",
            "/gps/*": "gps",
            
            # Trip Planning Service Routes - simplified
            "/trips": "trips", 
            "/trips/*": "trips",
            "/notifications": "trips",
            "/notifications/*": "trips",
        }

    def normalize_endpoint(self, endpoint: str) -> str:
        """Normalize endpoints for routing consistency"""
        # Remove /api prefix if present for simplified routing
        if endpoint.startswith("/api/"):
            endpoint = endpoint[4:]  # Remove "/api"
            
        return endpoint

    def get_service_for_endpoint(self, endpoint: str) -> str:
        """Determine target service based on endpoint pattern"""
        logger.debug(f"Looking for service for endpoint: {endpoint}")
        logger.debug(f"Available routing patterns: {list(self.routing_map.keys())}")
        
        # Normalize endpoint before matching
        normalized_endpoint = self.normalize_endpoint(endpoint)

        # First try exact matches
        if normalized_endpoint in self.routing_map:
            service = self.routing_map[normalized_endpoint]
            logger.debug(f"Found exact match: {normalized_endpoint} -> {service}")
            return service
        
        # Then try pattern matching
        for pattern, service in self.routing_map.items():
            if fnmatch.fnmatch(normalized_endpoint, pattern):
                logger.debug(f"Found pattern match: {normalized_endpoint} matches {pattern} -> {service}")
                return service
        
        logger.error(f"No service found for endpoint: {normalized_endpoint}")        
        raise ValueError(f"No service found for endpoint: {normalized_endpoint}")

    async def route_request(self, endpoint: str, method: str, data: Dict[Any, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate service and wait for response with resilience"""
        try:
            
            # Ensure response consumer is ready
            await self.response_manager.wait_for_ready()
            
            # Normalize endpoint for routing and downstream service
            normalized_endpoint = self.normalize_endpoint(endpoint)
            # Determine target service
            service = self.get_service_for_endpoint(endpoint)
            
            # Get circuit breaker for service
            circuit_breaker = circuit_breaker_manager.get_breaker(service)
            
            # Create correlation ID for tracking
            correlation_id = str(uuid.uuid4())
            # Create trace context using distributed tracer
            trace_context = distributed_tracer.create_trace_context(
                correlation_id, user_context.get("user_id", "unknown")
            )
            # Prepare request message
            request_msg = {
                "correlation_id": correlation_id,
                "endpoint": normalized_endpoint,
                "method": method,
                "data": data,
                "user_context": user_context,
                "timestamp": datetime.utcnow().isoformat(),
                "service": service,
                "trace_id": correlation_id
            }
            logger.info(f"Routing request {correlation_id} to service {service} for endpoint {normalized_endpoint}")
            # Send request with resilience patterns and circuit breaker
            start_time = time.time()
            try:
                response = await circuit_breaker.call(
                    lambda: resilience_manager.call_service_with_resilience(
                        service,
                        lambda: self.send_request_and_wait(service, request_msg, correlation_id),
                        retry_config={
                            "max_retries": 2,  # Reduced retries for user-facing requests
                            "base_delay": 0.5,
                            "max_delay": 10.0
                        }
                    )
                )
                # Log successful service call with distributed tracer
                duration = time.time() - start_time
                distributed_tracer.log_service_call(
                    correlation_id, service, f"{method} {normalized_endpoint}", duration, "success"
                )
                # Enhanced logging with performance metrics
                elapsed_time = time.time() - start_time
                logger.info(f"Request {correlation_id} completed successfully in {elapsed_time:.3f}s")
                # Record metrics for monitoring
                self._record_request_metrics(service, method, normalized_endpoint, elapsed_time, "success")
                # Complete trace with success
                distributed_tracer.complete_trace(correlation_id, {
                    "status": "success",
                    "duration_ms": elapsed_time * 1000,
                    "response_size": len(str(response)) if response else 0
                })
                return response
            except CircuitBreakerOpenError as e:
                logger.error(f"Circuit breaker open for {service}: {e}")
                raise HTTPException(status_code=503, detail=f"Service {service} is temporarily unavailable")
            except Exception as e:
                # Log failed service call with distributed tracer
                duration = time.time() - start_time
                distributed_tracer.log_service_call(
                    correlation_id, service, f"{method} {normalized_endpoint}", duration, "error", str(e)
                )
                # Complete trace with error
                distributed_tracer.complete_trace(correlation_id, "error")
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

    def _record_request_metrics(self, service: str, method: str, endpoint: str, duration: float, status: str):
        """Record request metrics for monitoring and analytics"""
        try:
            metrics_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "service": service,
                "method": method,
                "endpoint": endpoint,
                "duration_seconds": duration,
                "status": status
            }
            
            # Log metrics (in production, this could be sent to a metrics service)
            logger.info(f"METRICS: {json.dumps(metrics_data)}")
            
            # Could be extended to send to monitoring systems like Prometheus, DataDog, etc.
            
        except Exception as e:
            logger.warning(f"Failed to record metrics: {e}")

class ResponseCorrelationManager:
    """Manages correlation between requests and responses"""
    
    def __init__(self):
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.response_futures: Dict[str, asyncio.Future] = {}
        self._ready = asyncio.Event()
        self._consumer_task = None
        
    async def wait_for_ready(self, timeout: float = 30.0):
        """Wait for response consumer to be ready"""
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error("Response consumer failed to initialize within timeout")
            raise RuntimeError("Response consumer not ready")
        
    def register_pending_request(self, correlation_id: str) -> asyncio.Future:
        """Register a pending request and return future for response"""
        future = asyncio.Future()
        self.response_futures[correlation_id] = future
        return future
    
    async def wait_for_response(self, correlation_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for response with timeout and cleanup"""
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
            # Clean up to prevent memory leaks
            self.response_futures.pop(correlation_id, None)
    
    async def handle_response(self, response: Dict[str, Any]):
        """Handle incoming response and resolve corresponding future"""
        correlation_id = response.get("correlation_id")
        logger.info(f"[ResponseCorrelationManager] Received response: correlation_id={correlation_id}, status={response.get('status')}, keys={list(response.keys())}")
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
        """Consume responses from service response queue with enhanced error handling"""
        try:
            import aio_pika
            from rabbitmq import admin
            
            logger.info("Setting up response consumption...")
            
            # Use robust connection with reconnection logic
            connection = await aio_pika.connect_robust(
                admin.RABBITMQ_URL,
                heartbeat=60,
                blocked_connection_timeout=300,
            )
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=10)
            
            # Declare the service_responses exchange
            exchange = await channel.declare_exchange("service_responses", aio_pika.ExchangeType.DIRECT, durable=True)
            logger.info("Service responses exchange declared")
            
            # Declare and bind core.responses queue
            queue = await channel.declare_queue("core.responses", durable=True)
            await queue.bind(exchange, routing_key="core.responses")
            logger.info("Core responses queue bound to service_responses exchange")
            
            # Set up message handler with retry logic
            async def handle_response_message(message: aio_pika.IncomingMessage):
                try:
                    async with message.process(requeue=False):
                        response_data = json.loads(message.body.decode())
                        await self.handle_response(response_data)
                        logger.debug(f"Processed response: {response_data.get('correlation_id')}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in response message: {e}")
                except Exception as e:
                    logger.error(f"Error processing response message: {e}")
                    # Don't requeue to avoid infinite loops
            
            # Start consuming
            await queue.consume(handle_response_message, consumer_tag="core-response-consumer")
            logger.info("Core service started consuming responses from service_responses exchange")
            
            # Signal that consumer is ready
            self._ready.set()
            
            # Keep the connection alive with proper exception handling
            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Response consumption cancelled")
                raise
            finally:
                try:
                    await connection.close()
                except Exception as e:
                    logger.warning(f"Error closing RabbitMQ connection: {e}")
                
        except asyncio.CancelledError:
            logger.info("Response consumption task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error consuming responses: {e}")
            # Wait before retrying to avoid rapid retry loops
            await asyncio.sleep(5)
            logger.info("Retrying response consumption...")
            await self.consume_responses()


# Global instance
request_router = RequestRouter()
