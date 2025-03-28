import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TimeCache:
    """
    A simple in-memory cache implementation for time conversion results.
    """
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        logger.debug("Initialized TimeCache")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        Returns None if the key doesn't exist or if the entry has expired.
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if entry["expires"] < time.time():
            # Remove expired entry
            del self.cache[key]
            logger.debug(f"Cache entry expired for key: {key}")
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set a value in the cache with a specified TTL (time to live) in seconds.
        Default TTL is 1 hour.
        """
        self.cache[key] = {
            "value": value,
            "expires": time.time() + ttl
        }
        logger.debug(f"Cached value for key: {key}, TTL: {ttl}s")
    
    def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        self.cache.clear()
        logger.debug("Cache cleared")
    
    def remove(self, key: str) -> None:
        """
        Remove a specific key from the cache.
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Removed cache entry for key: {key}")
    
    def cleanup(self) -> int:
        """
        Remove all expired entries from the cache.
        Returns the number of entries removed.
        """
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if v["expires"] < now]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def size(self) -> int:
        """
        Return the current number of entries in the cache.
        """
        return len(self.cache)
    
    def stats(self) -> Dict[str, Any]:
        """
        Return statistics about the cache.
        """
        now = time.time()
        expired_count = sum(1 for v in self.cache.values() if v["expires"] < now)
        active_count = len(self.cache) - expired_count
        
        return {
            "total_entries": len(self.cache),
            "active_entries": active_count,
            "expired_entries": expired_count
        }
