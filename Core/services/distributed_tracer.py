"""
Distributed Tracing Service
Provides request tracing capabilities across microservices
"""

import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class TraceStatus(Enum):
    STARTED = "started"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class ServiceCall:
    """Represents a call to a service within a trace"""
    service_name: str
    operation: str
    start_time: float
    end_time: Optional[float] = None
    status: TraceStatus = TraceStatus.STARTED
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def complete(self, status: TraceStatus, error: str = None):
        """Complete the service call"""
        self.end_time = time.time()
        self.status = status
        self.error = error
        self.duration_ms = (self.end_time - self.start_time) * 1000

@dataclass
class TraceContext:
    """Represents a complete request trace"""
    trace_id: str
    correlation_id: str
    user_id: str
    start_time: float
    end_time: Optional[float] = None
    status: TraceStatus = TraceStatus.STARTED
    service_calls: List[ServiceCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_service_call(self, service_name: str, operation: str) -> ServiceCall:
        """Add a service call to the trace"""
        call = ServiceCall(
            service_name=service_name,
            operation=operation,
            start_time=time.time()
        )
        self.service_calls.append(call)
        return call
    
    def complete(self, status: TraceStatus, metadata: Dict[str, Any] = None):
        """Complete the trace"""
        self.end_time = time.time()
        self.status = status
        if metadata:
            self.metadata.update(metadata)
    
    def get_duration_ms(self) -> Optional[float]:
        """Get total trace duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for serialization"""
        return {
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status.value,
            "duration_ms": self.get_duration_ms(),
            "service_calls": [
                {
                    "service_name": call.service_name,
                    "operation": call.operation,
                    "start_time": call.start_time,
                    "end_time": call.end_time,
                    "status": call.status.value,
                    "duration_ms": call.duration_ms,
                    "error": call.error
                }
                for call in self.service_calls
            ],
            "metadata": self.metadata
        }

class DistributedTracer:
    """Manages distributed tracing across services"""
    
    def __init__(self):
        self._active_traces: Dict[str, TraceContext] = {}
        self._completed_traces: List[TraceContext] = []
        self._max_completed_traces = 1000  # Keep last 1000 traces
    
    def create_trace_context(self, correlation_id: str, user_id: str) -> TraceContext:
        """Create a new trace context"""
        trace_id = str(uuid.uuid4())
        
        trace = TraceContext(
            trace_id=trace_id,
            correlation_id=correlation_id,
            user_id=user_id,
            start_time=time.time()
        )
        
        self._active_traces[correlation_id] = trace
        logger.debug(f"Created trace context: {trace_id} for correlation: {correlation_id}")
        
        return trace
    
    def get_trace_context(self, correlation_id: str) -> Optional[TraceContext]:
        """Get existing trace context"""
        return self._active_traces.get(correlation_id)
    
    def log_service_call(
        self,
        correlation_id: str,
        service_name: str,
        operation: str,
        duration: float,
        status: str,
        error: str = None
    ):
        """Log a service call within a trace"""
        trace = self._active_traces.get(correlation_id)
        if not trace:
            logger.warning(f"No trace found for correlation_id: {correlation_id}")
            return
        
        # Find the most recent service call for this service or create new one
        service_call = None
        for call in reversed(trace.service_calls):
            if call.service_name == service_name and call.operation == operation and call.end_time is None:
                service_call = call
                break
        
        if not service_call:
            # Create new service call if not found
            service_call = trace.add_service_call(service_name, operation)
            service_call.start_time = time.time() - duration
        
        # Complete the service call
        trace_status = TraceStatus.SUCCESS if status == "success" else TraceStatus.ERROR
        service_call.complete(trace_status, error)
        
        logger.debug(f"Logged service call: {service_name}.{operation} - {status} in {duration*1000:.2f}ms")
    
    def complete_trace(self, correlation_id: str, metadata: Any = None):
        """Complete a trace"""
        trace = self._active_traces.pop(correlation_id, None)
        if not trace:
            logger.warning(f"No trace found for correlation_id: {correlation_id}")
            return
        
        # Determine overall status
        if isinstance(metadata, str) and metadata == "error":
            status = TraceStatus.ERROR
            metadata = {"error": "Request failed"}
        elif isinstance(metadata, dict):
            status = TraceStatus.SUCCESS if metadata.get("status") == "success" else TraceStatus.ERROR
        else:
            status = TraceStatus.SUCCESS
        
        trace.complete(status, metadata if isinstance(metadata, dict) else {})
        
        # Store completed trace
        self._completed_traces.append(trace)
        
        # Maintain trace history limit
        if len(self._completed_traces) > self._max_completed_traces:
            self._completed_traces = self._completed_traces[-self._max_completed_traces:]
        
        logger.info(f"Completed trace: {trace.trace_id} - {status.value} in {trace.get_duration_ms():.2f}ms")
    
    def get_trace_summary(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get trace summary for a correlation ID"""
        # Check active traces first
        trace = self._active_traces.get(correlation_id)
        if trace:
            return trace.to_dict()
        
        # Check completed traces
        for trace in reversed(self._completed_traces):
            if trace.correlation_id == correlation_id:
                return trace.to_dict()
        
        return None
    
    def get_recent_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent completed traces"""
        return [trace.to_dict() for trace in self._completed_traces[-limit:]]
    
    def get_trace_stats(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        active_count = len(self._active_traces)
        completed_count = len(self._completed_traces)
        
        # Calculate average duration from completed traces
        if self._completed_traces:
            durations = [trace.get_duration_ms() for trace in self._completed_traces if trace.get_duration_ms()]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Success rate
            successful = sum(1 for trace in self._completed_traces if trace.status == TraceStatus.SUCCESS)
            success_rate = (successful / completed_count) * 100 if completed_count > 0 else 0
        else:
            avg_duration = 0
            success_rate = 0
        
        return {
            "active_traces": active_count,
            "completed_traces": completed_count,
            "average_duration_ms": avg_duration,
            "success_rate_percent": success_rate
        }
    
    def cleanup_stale_traces(self, max_age_seconds: int = 300):
        """Clean up stale active traces (older than max_age_seconds)"""
        current_time = time.time()
        stale_traces = []
        
        for correlation_id, trace in self._active_traces.items():
            if current_time - trace.start_time > max_age_seconds:
                stale_traces.append(correlation_id)
        
        for correlation_id in stale_traces:
            trace = self._active_traces.pop(correlation_id)
            trace.complete(TraceStatus.TIMEOUT, {"reason": "trace_timeout"})
            self._completed_traces.append(trace)
            logger.warning(f"Cleaned up stale trace: {trace.trace_id}")
        
        if stale_traces:
            logger.info(f"Cleaned up {len(stale_traces)} stale traces")

# Global tracer instance
distributed_tracer = DistributedTracer()
