from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

APP_LABEL = 'crue_remisiones'


def crue_required(view_func):
	@wraps(view_func)
	@login_required
	def wrapper(request, *args, **kwargs):
		if request.user.is_superuser:
			return view_func(request, *args, **kwargs)
		perms = getattr(request.user, '_permisos_apps_cache', set())
		print (f"+++ {perms=}")
		if APP_LABEL in perms:
			return view_func(request, *args, **kwargs)
		return HttpResponseForbidden(
			'No tiene acceso a CRUE Remisiones. Contacte al administrador.'
		)
	return wrapper
