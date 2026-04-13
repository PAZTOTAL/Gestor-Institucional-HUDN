from django.db import connections
from django.db.utils import OperationalError
from django.core.cache import cache

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
                    # Attempt to get a connection and a cursor
                    with connections['readonly'].cursor() as cursor:
                        cursor.execute("SELECT 1")
                except (OperationalError, Exception) as e:
                    print(f"[ERROR] Fallo al conectar a la base de datos Hospital (readonly): {e}")
                    readonly_available = False
            
            # Cache the result for 1 minute
            cache.set(cache_key, readonly_available, 60)
        
        request.readonly_db_available = readonly_available
        
        response = self.get_response(request)
        return response
