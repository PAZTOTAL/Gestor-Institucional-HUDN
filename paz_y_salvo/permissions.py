"""
DRF permissions para Paz y Salvo usando JWT Bearer tokens.
"""
from rest_framework.permissions import BasePermission
from .auth import decode_token


def _get_user_from_request(request):
    """Extrae y decodifica el JWT del header Authorization: Bearer <token>."""
    auth = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    try:
        return decode_token(token)
    except ValueError:
        return None


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        user = _get_user_from_request(request)
        if user:
            request.pys_user = user
            return True
        return False


def require_roles(*roles):
    """Factory: devuelve una clase Permission que exige uno de los roles dados."""
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            user = _get_user_from_request(request)
            if not user:
                return False
            if user.get('rol') not in roles:
                return False
            request.pys_user = user
            return True
    return RolePermission
