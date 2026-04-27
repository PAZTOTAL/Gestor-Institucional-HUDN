from django.core.cache import cache
import logging
import threading

logger = logging.getLogger(__name__)

# Rutas que no necesitan el check de BD
_SKIP_PATHS = ('/login', '/logout', '/accounts/login', '/accounts/logout', '/admin/login',
               '/static/', '/favicon')

_check_lock = threading.Lock()


def _check_databases_connectivity():
    """Verifica las bases de datos en un hilo aparte con timeout propio."""
    import socket
    # Timeout de socket para que no cuelgue el hilo más de 5 segundos
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(5)
    try:
        from django.db import connections as _conns

        # Check Readonly (DGEMPRES03)
        try:
            conn_ro = _conns['readonly']
            conn_ro.ensure_connection()
            with conn_ro.cursor() as cursor:
                cursor.execute("SELECT 1")
            conn_ro.close()
            cache.set('readonly_db_available', True, 3600)
        except Exception as e:
            logger.warning("BD readonly no disponible: %s", e)
            cache.set('readonly_db_available', False, 120)
            try:
                _conns['readonly'].close()
            except Exception:
                pass

        # Check Default (GestorInstitucional)
        try:
            conn_def = _conns['default']
            conn_def.ensure_connection()
            with conn_def.cursor() as cursor:
                cursor.execute("SELECT 1")
            conn_def.close()
            cache.set('default_db_available', True, 3600)
        except Exception as e:
            logger.warning("BD default no disponible: %s", e)
            cache.set('default_db_available', False, 120)
            try:
                _conns['default'].close()
            except Exception:
                pass
    finally:
        socket.setdefaulttimeout(old_timeout)
        cache.delete('db_check_running')


class DatabaseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        
        # 0. Saltar validaciones para rutas críticas (Login/Logout/Admin)
        if any(path.startswith(p) for p in _SKIP_PATHS):
            request.readonly_db_available = True
            request.default_db_available = True
            request.db_caidas = None
            return self.get_response(request)

        # Obtener estados del cache
        readonly_ok = cache.get('readonly_db_available')
        default_ok = cache.get('default_db_available')

        # Rutas de autenticación y estáticos no necesitan el check
        if not any(path.startswith(p) for p in _SKIP_PATHS):
            readonly_ok = cache.get('readonly_db_available')
            default_ok  = cache.get('default_db_available')

            if readonly_ok is None or default_ok is None:
                if readonly_ok is None:
                    readonly_ok = True
                if default_ok is None:
                    default_ok = True

                # Lanzar hilo solo si no hay uno en curso
                if not cache.get('db_check_running') and _check_lock.acquire(blocking=False):
                    try:
                        cache.set('db_check_running', True, 30)
                        t = threading.Thread(target=_check_databases_connectivity, daemon=True)
                        t.start()
                    finally:
                        _check_lock.release()
        else:
            readonly_ok = cache.get('readonly_db_available', True)
            default_ok  = cache.get('default_db_available', True)

        request.readonly_db_available = readonly_ok
        request.default_db_available  = default_ok

        caidas = []
        if not readonly_ok:
            caidas.append("DGEMPRES03 (Dinámica Nexus)")
        if not default_ok:
            caidas.append("GestorInstitucional (Producción)")
        request.db_caidas = ", ".join(caidas) if caidas else None

        response = self.get_response(request)
        return response

class SecurityProtectionMiddleware:
    """
    Middleware para protección adicional contra ataques comunes:
    - Bloqueo de User-Agents sospechosos (Scanners, Bots).
    - Limitación básica de peticiones (Rate Limiting por IP).
    - Detección de patrones maliciosos en parámetros.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self._blocked_agents = [
            'sqlmap', 'nmap', 'nikto', 'dirbuster', 'gobuster', 'burp', 'hydra',
            'acunetix', 'metasploit', 'zaproxy', 'nessus', 'w3af'
        ]

    def __call__(self, request):
        # 1. Verificar User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if any(agent in user_agent for agent in self._blocked_agents):
            logger.warning(f"Bloqueado User-Agent sospechoso: {user_agent} desde {request.META.get('REMOTE_ADDR')}")
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Acceso denegado por políticas de seguridad.")

        # 2. Rate Limiting Básico (Usando cache)
        ip = request.META.get('REMOTE_ADDR')
        cache_key = f'ratelimit_{ip}'
        requests_count = cache.get(cache_key, 0)
        
        # Límite: 100 peticiones cada 60 segundos por IP
        if requests_count > 100:
            logger.warning(f"Rate Limit excedido para IP: {ip}")
            from django.http import HttpResponse
            return HttpResponse("Demasiadas peticiones. Por favor, espere un minuto.", status=429)
        
        cache.set(cache_key, requests_count + 1, 60)

        # 3. Filtro básico de inyección en URLs (XSS/SQLi simple)
        path = request.path.lower()
        malicious_patterns = ["<script", "javascript:", "union select", "waitfor delay", "sysdatabases", "sysobjects"]
        if any(pattern in path for pattern in malicious_patterns):
             logger.warning(f"Bloqueado patrón malicioso en URL: {path} desde {ip}")
             from django.http import HttpResponseBadRequest
             return HttpResponseBadRequest("Petición malformada o potencialmente peligrosa.")

        return self.get_response(request)
