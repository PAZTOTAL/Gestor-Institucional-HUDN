from django.db import connections
from django.db.utils import OperationalError
from django.core.cache import cache
import logging
import threading

logger = logging.getLogger(__name__)

# Rutas que no necesitan el check de BD (login/logout son críticas en velocidad)
_SKIP_PATHS = ('/login', '/logout', '/accounts/login', '/accounts/logout', '/admin/login')

def _check_readonly_db_background():
    """Verifica la BD readonly en un hilo aparte para no bloquear el request."""
    try:
        conn = connections['readonly']
        conn.ensure_connection()
        cache.set('readonly_db_available', True, 3600)  # 1 hora si OK
    except Exception as e:
        logger.warning(f"BD readonly no disponible: {e}")
        cache.set('readonly_db_available', False, 120)  # Reintentar en 2 min si falla
    finally:
        try:
            connections['readonly'].close()
        except Exception:
            pass

class DatabaseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Saltar el check en rutas de autenticación para no demorar login/logout
        path = request.path_info
        if any(path.startswith(p) for p in _SKIP_PATHS):
            request.readonly_db_available = cache.get('readonly_db_available', True)
            return self.get_response(request)

        cache_key = 'readonly_db_available'
        readonly_available = cache.get(cache_key)

        if readonly_available is None:
            # Usar el último valor conocido (True por defecto) y verificar en background
            readonly_available = True
            cache.set(cache_key, readonly_available, 30)  # Placeholder 30s
            t = threading.Thread(target=_check_readonly_db_background, daemon=True)
            t.start()

        request.readonly_db_available = readonly_available

        response = self.get_response(request)
        return response
