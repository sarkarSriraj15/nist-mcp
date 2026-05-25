import os
import logging
import functools
import diskcache

logger = logging.getLogger("nist-mcp")

CACHE_DIR = os.environ.get("NIST_CACHE_DIR", os.path.expanduser("~/.cache/nist-mcp"))
TTL_SECONDS = int(os.environ.get("NIST_CACHE_TTL_SECONDS", "86400"))

# Initialize Cache
try:
    cache = diskcache.Cache(CACHE_DIR)
except Exception as e:
    logger.warning(f"Failed to initialize diskcache at {CACHE_DIR}: {e}. Caching will be disabled.")
    cache = None

def cached(fn):
    """
    Decorator to cache function results using diskcache.
    Supports simple JSON-serializable arguments.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if cache is None:
            return fn(*args, **kwargs)
        
        # Build cache key from function name and arguments
        # Simple representation since we only use strings/integers as parameters
        key_parts = [fn.__name__]
        for arg in args:
            key_parts.append(str(arg))
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        key = ":".join(key_parts)
        
        try:
            val = cache.get(key)
            if val is not None:
                logger.debug(f"Cache hit for key: {key}")
                return val
        except Exception as e:
            logger.warning(f"Cache lookup failed for key {key}: {e}")
        
        # Calculate result
        result = fn(*args, **kwargs)
        
        try:
            cache.set(key, result, expire=TTL_SECONDS)
            logger.debug(f"Cache set for key: {key} (TTL: {TTL_SECONDS}s)")
        except Exception as e:
            logger.warning(f"Cache write failed for key {key}: {e}")
            
        return result
        
    return wrapper
