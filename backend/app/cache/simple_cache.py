"""
Simple in-memory cache implementation for HR Search application.

Thread-safe caching with TTL and LRU eviction. Designed to be lightweight
and suitable for small to medium workloads without external dependencies.
"""

import time
import threading
import hashlib
import inspect
import json
from typing import Dict, Any, Optional, Callable
from functools import wraps
from collections import OrderedDict

from ..logging_config import get_logger

logger = get_logger("cache")


class SimpleCache:
    """Thread-safe in-memory cache with TTL and LRU eviction."""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of entries before LRU eviction
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache: OrderedDict[str, tuple] = OrderedDict()  # (value, timestamp, ttl)
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self.lock:
            if key in self.cache:
                value, timestamp, ttl = self.cache[key]
                if time.time() - timestamp < ttl:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.hits += 1
                    return value
                else:
                    # Expired, remove it
                    del self.cache[key]
                    self.misses += 1
            else:
                self.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        with self.lock:
            # Remove if already exists
            if key in self.cache:
                del self.cache[key]
            
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            # Store with timestamp
            cache_ttl = ttl if ttl is not None else self.default_ttl
            self.cache[key] = (value, time.time(), cache_ttl)
            
            logger.debug(
                "Cache set",
                extra={
                    "key": key[:50] + "..." if len(key) > 50 else key,
                    "ttl": cache_ttl,
                    "cache_size": len(self.cache),
                }
            )
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests,
            }
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        with self.lock:
            current_time = time.time()
            expired_keys = []
            
            for key, (_, timestamp, ttl) in self.cache.items():
                if current_time - timestamp >= ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug(
                    f"Cleaned up {len(expired_keys)} expired cache entries"
                )
            
            return len(expired_keys)


# Global cache instance
cache = SimpleCache(default_ttl=300, max_size=1000)


def hash_args(args: tuple, kwargs: dict) -> str:
    """Generate hash for function arguments."""
    args_str = json.dumps(args, sort_keys=True, default=str)
    kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
    combined = f"{args_str}:{kwargs_str}"

    return hashlib.md5(combined.encode()).hexdigest()[:16]


def _is_method(func: Callable) -> bool:
    """Return True if func's first parameter is 'self' or 'cls'."""
    try:
        params = list(inspect.signature(func).parameters)
    except (TypeError, ValueError):
        return False
    return bool(params) and params[0] in ("self", "cls")


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results.

    Skips the first positional arg when it is `self`/`cls`, so cache keys
    don't depend on instance identity. FastAPI builds a fresh service per
    request, and keying off `str(self)` (memory address) would miss every time.

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable):
        skip_first = _is_method(func)
        cache_name = f"{func.__module__}.{func.__qualname__}"

        def _build_key(args: tuple, kwargs: dict) -> str:
            key_args = args[1:] if skip_first else args
            return f"{key_prefix}:{cache_name}:{hash_args(key_args, kwargs)}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = _build_key(args, kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(
                    f"Cache hit for {func.__name__}",
                    extra={"cache_key": cache_key[:50]}
                )
                return cached_value

            # Call function and cache result
            logger.debug(
                f"Cache miss for {func.__name__}",
                extra={"cache_key": cache_key[:50]}
            )
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = _build_key(args, kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(
                    f"Cache hit for {func.__name__}",
                    extra={"cache_key": cache_key[:50]}
                )
                return cached_value
            
            # Call function and cache result
            logger.debug(
                f"Cache miss for {func.__name__}",
                extra={"cache_key": cache_key[:50]}
            )
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
