"""
Decoradores de acceso para la aplicación crue_traslados.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

APP_LABEL = 'crue'

def checkCrue (label, permisos):
	return any (label.upper() in x.upper() for x in permisos)


def crue_required (view_func):
	"""Restringe el acceso a usuarios con permiso para la app crue_traslados."""
	@wraps (view_func)
	@login_required
	def wrapper (request, *args, **kwargs):
		"""Verifica permisos del usuario antes de ejecutar la vista."""
		if request.user.is_superuser:
			return view_func (request, *args, **kwargs)
		perms = getattr (request.user, '_permisos_apps_cache', set ())
		if checkCrue (APP_LABEL, perms):
			return view_func (request, *args, **kwargs)
		return HttpResponseForbidden (
			'No tiene acceso a CRUE Traslados. Contacte al administrador.'
		)
	return wrapper



class CrueRequiredMixin:
	"""Mixin para CBVs que restringe acceso a usuarios con permiso para crue_traslados."""

	def dispatch (self, request, *args, **kwargs):
		"""Verifica permisos antes de despachar la vista."""
		if not request.user.is_authenticated:
			from django.contrib.auth.views import redirect_to_login
			return redirect_to_login (request.get_full_path ())
		if request.user.is_superuser:
			return super ().dispatch (request, *args, **kwargs)
		perms = getattr (request.user, '_permisos_apps_cache', set ())
		if checkCrue (APP_LABEL, perms):
			return super ().dispatch (request, *args, **kwargs)
		return HttpResponseForbidden (
			'No tiene acceso a CRUE Traslados. Contacte al administrador.'
		)
