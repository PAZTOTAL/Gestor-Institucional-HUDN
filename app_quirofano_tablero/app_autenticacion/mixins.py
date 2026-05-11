from django.shortcuts import redirect


class LoginRequeridoMixin:
	"""Protege vistas privadas verificando que el usuario tenga sesión activa."""

	def dispatch (self, request, *args, **kwargs):
		"""Redirige a login si no hay email en la sesión."""
		if not request.session.get ('email'):
			return redirect ('login')
		return super ().dispatch (request, *args, **kwargs)
