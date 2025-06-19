"""
Circuit Breaker and Retry Logic for SAMFMS Core
Provides resilience patterns for service communication
"""

import asyncio
import time
import logging
from typing import Callable, Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    timeout: int = 60  # seconds
    half_open_max_calls: int = 3

class ServiceCircuitBreaker:
    """Circuit breaker implementation for service calls"""
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def call_service(self, service_call: Callable[[], Any]) -> Any:
        """Execute service call with circuit breaker protection"""
        async with self._lock:
            current_time = time.time()
            
            # Check if we should transition from OPEN to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if (self.last_failure_time and 
                    current_time - self.last_failure_time > self.config.timeout):
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker for {self.service_name} transitioning to HALF_OPEN")
                else:
                    self._raise_circuit_open_error()
            
            # Check if we're in HALF_OPEN and have exceeded max calls
            elif self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    self._raise_circuit_open_error()
                self.half_open_calls += 1
        
        # Execute the service call
        try:
            result = await service_call()
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful service call"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker for {self.service_name} transitioning to CLOSED")
            
            self.failure_count = 0
            self.last_failure_time = None
    
    async def _on_failure(self):
        """Handle failed service call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning(f"Circuit breaker for {self.service_name} transitioning to OPEN")
            
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker for {self.service_name} back to OPEN from HALF_OPEN")
    
    def _raise_circuit_open_error(self):
        """Raise error when circuit is open"""
        raise HTTPException(
            status_code=503,
            detail=f"Service {self.service_name} circuit breaker is OPEN"
        )
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "service_name": self.service_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "half_open_calls": self.half_open_calls if self.state == CircuitState.HALF_OPEN else None
        }

class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    @staticmethod
    async def retry_with_backoff(
        func: Callable[[], Any],
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ) -> Any:
        """
        Retry function with exponential backoff
        
        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Multiplier for delay between retries
            jitter: Add random jitter to delays
        """
        import random
        
        last_exception = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                return await func()
            except Exception as e:
                last_exception = e
                
                if attempt == max_retries:
                    logger.error(f"All retry attempts failed. Last error: {e}")
                    raise
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                
                # Add jitter to prevent thundering herd
                if jitter:
                    delay *= (0.5 + random.random() * 0.5)
                
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception

class ServiceUnavailableException(Exception):
    """Exception raised when service is unavailable"""
    pass

class ServiceResilienceManager:
    """Manages circuit breakers and retry policies for all services"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, ServiceCircuitBreaker] = {}
        self.default_circuit_config = CircuitBreakerConfig()
        
    def get_circuit_breaker(self, service_name: str) -> ServiceCircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = ServiceCircuitBreaker(
                service_name, self.default_circuit_config
            )
        return self.circuit_breakers[service_name]
    
    async def call_service_with_resilience(
        self,
        service_name: str,
        service_call: Callable[[], Any],
        retry_config: Dict[str, Any] = None
    ) -> Any:
        """
        Call service with circuit breaker and retry protection
        
        Args:
            service_name: Name of the service
            service_call: Async function to call the service
            retry_config: Optional retry configuration
        """
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        # Default retry configuration
        default_retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 30.0,
            "backoff_factor": 2.0,
            "jitter": True
        }
        
        retry_config = {**default_retry_config, **(retry_config or {})}
        
        async def resilient_call():
            return await circuit_breaker.call_service(service_call)
        
        return await RetryHandler.retry_with_backoff(
            resilient_call,
            **retry_config
        )
    
    def get_all_circuit_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        return {
            name: breaker.get_state() 
            for name, breaker in self.circuit_breakers.items()
        }
    
    def reset_circuit_breaker(self, service_name: str):
        """Reset specific circuit breaker"""
        if service_name in self.circuit_breakers:
            breaker = self.circuit_breakers[service_name]
            breaker.state = CircuitState.CLOSED
            breaker.failure_count = 0
            breaker.last_failure_time = None
            breaker.half_open_calls = 0
            logger.info(f"Reset circuit breaker for {service_name}")
    
    def reset_all_circuit_breakers(self):
        """Reset all circuit breakers"""
        for service_name in self.circuit_breakers:
            self.reset_circuit_breaker(service_name)
        logger.info("Reset all circuit breakers")

# Global instance
resilience_manager = ServiceResilienceManager()


class RequestTracer:
    """Distributed tracing for requests across services"""
    
    def __init__(self):
        self.active_traces: Dict[str, Dict[str, Any]] = {}
    
    def create_trace_context(self, request_id: str, user_id: str) -> Dict[str, Any]:
        """Create new trace context"""
        trace_context = {
            "trace_id": request_id,
            "user_id": user_id,
            "start_time": time.time(),
            "services_called": [],
            "total_duration": 0,
            "status": "active"
        }
        
        self.active_traces[request_id] = trace_context
        return trace_context
    
    def log_service_call(
        self,
        trace_id: str,
        service: str,
        operation: str,
        duration: float,
        status: str = "success",
        error: str = None
    ):
        """Log service call in trace"""
        if trace_id in self.active_traces:
            trace = self.active_traces[trace_id]
            
            service_call = {
                "service": service,
                "operation": operation,
                "duration": duration,
                "status": status,
                "error": error,
                "timestamp": time.time()
            }
            
            trace["services_called"].append(service_call)
            
            logger.info(
                f"Trace {trace_id}: {service}.{operation} took {duration:.3f}s ({status})",
                extra={
                    "trace_id": trace_id,
                    "service": service,
                    "operation": operation,
                    "duration": duration,
                    "status": status
                }
            )
    
    def complete_trace(self, trace_id: str, status: str = "completed"):
        """Complete trace and calculate totals"""
        if trace_id in self.active_traces:
            trace = self.active_traces[trace_id]
            trace["total_duration"] = time.time() - trace["start_time"]
            trace["status"] = status
            
            logger.info(
                f"Trace {trace_id} completed in {trace['total_duration']:.3f}s "
                f"with {len(trace['services_called'])} service calls",
                extra={
                    "trace_id": trace_id,
                    "total_duration": trace["total_duration"],
                    "service_calls": len(trace["services_called"]),
                    "status": status
                }
            )
            
            # Keep trace for a short time for debugging
            asyncio.create_task(self._cleanup_trace(trace_id, delay=300))  # 5 minutes
    
    async def _cleanup_trace(self, trace_id: str, delay: int):
        """Clean up trace after delay"""
        await asyncio.sleep(delay)
        self.active_traces.pop(trace_id, None)
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get trace information"""
        return self.active_traces.get(trace_id)
    
    def get_active_traces(self) -> Dict[str, Dict[str, Any]]:
        """Get all active traces"""
        return self.active_traces.copy()

# Global instance
request_tracer = RequestTracer()
