from django.db import connections
from django.db.utils import OperationalError
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class DatabaseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check connection to 'readonly' database
        # We use a cache to avoid checking on every single request (performance)
        cache_key = 'readonly_db_available'
        readonly_available = cache.get(cache_key)
        
        if readonly_available is None:
            readonly_available = True
            if 'readonly' in connections:
                try:
                    conn = connections['readonly']
                    # Use ensure_connection for a faster check
                    conn.ensure_connection()
                    readonly_available = True
                except (OperationalError, Exception) as e:
                    logger.error(f"Fallo al conectar a la base de datos Hospital (readonly): {e}")
                    readonly_available = False
            
            # Cache the result for 5 minutes (was 1 minute - too aggressive for a health check)
            cache.set(cache_key, readonly_available, 300)
        
        request.readonly_db_available = readonly_available
        
        response = self.get_response(request)
        return response
