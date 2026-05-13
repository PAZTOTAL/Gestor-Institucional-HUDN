"""Permisos DRF para el módulo APC usando JWT Bearer tokens."""
from rest_framework.permissions import BasePermission
from .auth import decode_token


def _get_user(request):
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
        user = _get_user(request)
        if user:
            request.apc_user = user
            return True
        return False


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = _get_user(request)
        if user and user.get('rol') == 'apc_admin':
            request.apc_user = user
            return True
        return False


def require_roles(*roles):
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            user = _get_user(request)
            if not user:
                return False
            if user.get('rol') not in roles:
                return False
            request.apc_user = user
            return True
    return RolePermission
