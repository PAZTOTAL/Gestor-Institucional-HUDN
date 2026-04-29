import re
from django.conf import settings
from django.shortcuts import render, redirect
from django.views import View

PATRON_EMAIL = re.compile (r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class LoginVista (View):
	"""Gestiona el inicio de sesión por correo electrónico."""

	def get (self, request):
		"""Muestra el formulario de login."""
		return render (request, 'autenticacion/login.html')

	def post (self, request):
		"""Valida el email y crea la sesión si está autorizado."""
		email = request.POST.get ('email', '').strip ()
		if not PATRON_EMAIL.match (email):
			return render (request, 'autenticacion/login.html', {'error': 'Correo electrónico no válido.'})
		if not self._emailAutorizado (email):
			return render (request, 'autenticacion/login.html', {'error': 'Correo electrónico no autorizado.'})
		request.session ['email'] = email
		return redirect ('gestion')

	def _emailAutorizado (self, email: str) -> bool:
		print (f"+++ _emailAutorizado{email=}")
		"""Verifica whitelist o dominio permitido desde settings."""
		whitelist = getattr (settings, 'EMAIL_WHITELIST', [])
		print (f"+++ {whitelist=}")
		dominio   = getattr (settings, 'EMAIL_DOMINIO_PERMITIDO', None)
		print (f"+++ {dominio=}")
		if whitelist:
			return email in whitelist
		if dominio:
			return email.endswith (f'@{dominio}')
		return False


class LogoutVista (View):
	"""Gestiona el cierre de sesión."""

	def post (self, request):
		"""Limpia la sesión y redirige al login."""
		request.session.flush ()
		return redirect ('login')
