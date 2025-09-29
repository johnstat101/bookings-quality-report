from django.core.cache import cache
from django.conf import settings
import hashlib

def get_cache_key(prefix, *args):
    """Generate consistent cache keys"""
    key_data = '|'.join(str(arg) for arg in args)
    hash_key = hashlib.md5(key_data.encode()).hexdigest()
    return f"{prefix}:{hash_key}"

def cache_analytics_data(key, data, timeout=300):
    """Cache analytics data with 5-minute default timeout"""
    cache.set(key, data, timeout)
    return data

def get_cached_analytics(key):
    """Retrieve cached analytics data"""
    return cache.get(key)