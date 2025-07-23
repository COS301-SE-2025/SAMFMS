"""
Request Deduplication Service
Prevents duplicate requests from reaching service blocks
"""

import hashlib
import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DeduplicationConfig:
    """Configuration for request deduplication"""
    content_ttl: float = 60.0      # Content-based deduplication TTL (seconds)
    correlation_ttl: float = 300.0  # Correlation-based deduplication TTL (seconds)
    max_cache_size: int = 10000    # Maximum cached requests

class RequestDeduplicator:
    """Handles request deduplication at the Core level"""
    
    def __init__(self, config: DeduplicationConfig = None):
        self.config = config or DeduplicationConfig()
        
        # Cache for tracking requests
        self._correlation_cache: Dict[str, float] = {}  # correlation_id -> timestamp
        self._content_cache: Dict[str, Tuple[str, float]] = {}  # content_hash -> (correlation_id, timestamp)
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Start cleanup task
        self._cleanup_task = None
    
    async def start(self):
        """Start the deduplication service"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("Request deduplicator started")
    
    async def stop(self):
        """Stop the deduplication service"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Request deduplicator stopped")
    
    def _generate_content_hash(self, request_data: Dict[str, Any]) -> str:
        """Generate hash for request content"""
        # Extract relevant fields for hashing (exclude correlation_id and timestamp)
        content_for_hash = {
            "method": request_data.get("method"),
            "endpoint": request_data.get("endpoint"),
            "data": request_data.get("data", {}),
            "user_context": {
                k: v for k, v in request_data.get("user_context", {}).items() 
                if k not in ["correlation_id", "timestamp"]
            }
        }
        
        # Create deterministic hash
        content_str = json.dumps(content_for_hash, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    async def check_and_record_request(
        self, 
        correlation_id: str, 
        request_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Check if request is duplicate and record it
        
        Returns:
            None if request is new (should be processed)
            str if request is duplicate (contains reason)
        """
        async with self._lock:
            current_time = time.time()
            
            # Check correlation ID-based deduplication
            if correlation_id in self._correlation_cache:
                request_age = current_time - self._correlation_cache[correlation_id]
                if request_age < self.config.correlation_ttl:
                    logger.warning(f"Duplicate request detected (correlation_id): {correlation_id}")
                    return f"Duplicate correlation_id within {self.config.correlation_ttl}s"
            
            # Check content-based deduplication
            content_hash = self._generate_content_hash(request_data)
            if content_hash in self._content_cache:
                existing_correlation_id, existing_timestamp = self._content_cache[content_hash]
                content_age = current_time - existing_timestamp
                if content_age < self.config.content_ttl:
                    logger.warning(f"Duplicate request detected (content): {correlation_id} matches {existing_correlation_id}")
                    return f"Duplicate content within {self.config.content_ttl}s"
            
            # Record the request
            self._correlation_cache[correlation_id] = current_time
            self._content_cache[content_hash] = (correlation_id, current_time)
            
            # Check cache size limits
            if len(self._correlation_cache) > self.config.max_cache_size:
                await self._emergency_cleanup()
            
            return None  # Not a duplicate
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired cache entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                await self._cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during deduplication cleanup: {e}")
    
    async def _cleanup_expired_entries(self):
        """Remove expired entries from cache"""
        async with self._lock:
            current_time = time.time()
            
            # Clean correlation cache
            expired_correlations = [
                correlation_id for correlation_id, timestamp in self._correlation_cache.items()
                if current_time - timestamp > self.config.correlation_ttl
            ]
            for correlation_id in expired_correlations:
                del self._correlation_cache[correlation_id]
            
            # Clean content cache
            expired_content = [
                content_hash for content_hash, (_, timestamp) in self._content_cache.items()
                if current_time - timestamp > self.config.content_ttl
            ]
            for content_hash in expired_content:
                del self._content_cache[content_hash]
            
            if expired_correlations or expired_content:
                logger.debug(f"Cleaned up {len(expired_correlations)} correlations and {len(expired_content)} content hashes")
    
    async def _emergency_cleanup(self):
        """Emergency cleanup when cache is too large"""
        logger.warning(f"Cache size exceeded {self.config.max_cache_size}, performing emergency cleanup")
        
        current_time = time.time()
        
        # Remove oldest 20% of entries
        correlation_items = list(self._correlation_cache.items())
        correlation_items.sort(key=lambda x: x[1])  # Sort by timestamp
        remove_count = len(correlation_items) // 5
        
        for correlation_id, _ in correlation_items[:remove_count]:
            del self._correlation_cache[correlation_id]
        
        # Also clean content cache
        content_items = list(self._content_cache.items())
        content_items.sort(key=lambda x: x[1][1])  # Sort by timestamp
        remove_count = len(content_items) // 5
        
        for content_hash, _ in content_items[:remove_count]:
            del self._content_cache[content_hash]
        
        logger.info(f"Emergency cleanup completed, cache sizes: correlations={len(self._correlation_cache)}, content={len(self._content_cache)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        return {
            "correlation_cache_size": len(self._correlation_cache),
            "content_cache_size": len(self._content_cache),
            "config": {
                "content_ttl": self.config.content_ttl,
                "correlation_ttl": self.config.correlation_ttl,
                "max_cache_size": self.config.max_cache_size
            }
        }

# Global deduplicator instance
request_deduplicator = RequestDeduplicator()
