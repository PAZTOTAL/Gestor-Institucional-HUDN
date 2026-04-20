from django.db import connections
from django.db.utils import OperationalError
from django.core.cache import cache
import logging
import threading

logger = logging.getLogger(__name__)

# Rutas que no necesitan el check de BD (login/logout son críticas en velocidad)
_SKIP_PATHS = ('/login', '/logout', '/accounts/login', '/accounts/logout', '/admin/login')

def _check_databases_connectivity():
    """Verifica las bases de datos en un hilo aparte."""
    # Check Readonly (DGEMPRES03)
    conn_ro = connections['readonly']
    try:
        conn_ro.ensure_connection()
        # Intentar una consulta rápida para validar que realmente responde
        with conn_ro.cursor() as cursor:
            cursor.execute("SELECT 1")
        cache.set('readonly_db_available', True, 3600)
    except Exception as e:
        logger.warning(f"BD readonly no disponible: {e}")
        cache.set('readonly_db_available', False, 120)
        try: conn_ro.close()
        except: pass
    
    # Check Default (GestorInstitucional)
    conn_def = connections['default']
    try:
        conn_def.ensure_connection()
        with conn_def.cursor() as cursor:
            cursor.execute("SELECT 1")
        cache.set('default_db_available', True, 3600)
    except Exception as e:
        logger.warning(f"BD default no disponible: {e}")
        cache.set('default_db_available', False, 120)
        try: conn_def.close()
        except: pass

class DatabaseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        
        # Obtener estados del cache
        readonly_ok = cache.get('readonly_db_available')
        default_ok = cache.get('default_db_available')

        if readonly_ok is None or default_ok is None:
            # Si alguno es None, iniciamos verificación en background
            if readonly_ok is None: readonly_ok = True
            if default_ok is None: default_ok = True
            
            # Solo disparamos el hilo si no hay uno ya corriendo recientemente (caché de control)
            if not cache.get('db_check_running'):
                cache.set('db_check_running', True, 30)
                t = threading.Thread(target=_check_databases_connectivity, daemon=True)
                t.start()

        # Pasar estados al request para el template
        request.readonly_db_available = readonly_ok
        request.default_db_available = default_ok
        
        # Identificar bases caídas para mostrar nombres
        caidas = []
        if not readonly_ok: caidas.append("DGEMPRES03 (Dinámica Nexus)")
        if not default_ok: caidas.append("GestorInstitucional (Producción)")
        
        request.db_caidas = ", ".join(caidas) if caidas else None

        response = self.get_response(request)
        return response
