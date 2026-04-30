"""CORS simple para rutas /api/pys/ — permite llamadas desde el frontend React."""
from django.conf import settings


class PysCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        origins = getattr(settings, 'CORS_ALLOWED_ORIGINS_PYS', ['http://localhost:5173'])
        self.allowed_origins = set(origins)

    def __call__(self, request):
        origin = request.META.get('HTTP_ORIGIN', '')

        if self._is_pys_path(request.path) and request.method == 'OPTIONS':
            response = self._preflight(origin)
            return response

        response = self.get_response(request)

        if self._is_pys_path(request.path):
            self._add_cors_headers(response, origin)

        return response

    _PYS_PREFIXES = (
        '/api/auth/', '/api/paz-salvos', '/api/validar',
        '/api/solicitudes', '/api/admin/', '/api/logs/',
    )

    def _is_pys_path(self, path):
        return any(path.startswith(p) for p in self._PYS_PREFIXES)

    def _preflight(self, origin):
        from django.http import HttpResponse
        response = HttpResponse()
        response.status_code = 204
        self._add_cors_headers(response, origin)
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-CSRFToken'
        response['Access-Control-Max-Age'] = '86400'
        return response

    def _add_cors_headers(self, response, origin):
        if origin in self.allowed_origins or '*' in self.allowed_origins:
            response['Access-Control-Allow-Origin'] = origin or '*'
        else:
            response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
