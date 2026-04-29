import pytest
import factory

from django.test import Client
from django.urls import reverse

from .models import EstadoQuirurgico, Paciente, Sesion


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

class PacienteFactory (factory.django.DjangoModelFactory):
	"""Factory para crear instancias de Paciente en tests de vistas."""

	class Meta:
		model = Paciente

	identificacion = factory.Sequence (lambda n: f"VIS-{n:04d}")
	nombre         = factory.Sequence (lambda n: f"Nombre Paciente {n}")
	origen         = 'PROGRAMADO'


class SesionFactory (factory.django.DjangoModelFactory):
	"""Factory para crear instancias de Sesion en tests de vistas."""

	class Meta:
		model = Sesion

	paciente = factory.SubFactory (PacienteFactory)
	estado   = EstadoQuirurgico.EN_PREPARACION
	oculto   = False


# ---------------------------------------------------------------------------
# Tests de vistas
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTableroVista:
	"""Tests para la vista pública del tablero."""

	def test_tablero_carga_sin_autenticacion (self):
		"""GET /tablero/ retorna HTTP 200 sin requerir sesión activa."""
		cliente = Client ()

		respuesta = cliente.get (reverse ('tablero'))

		assert respuesta.status_code == 200


@pytest.mark.django_db
class TestTableroFragmentoVista:
	"""Tests para la vista de fragmento del tablero."""

	def test_fragmento_no_retorna_sesiones_ocultas (self):
		"""GET /tablero/fragmento/ no incluye sesiones con oculto=True en la respuesta."""
		sesion = SesionFactory (oculto=True)
		cliente = Client ()

		respuesta = cliente.get (reverse ('tablero-fragmento'))

		assert sesion.paciente.identificacion not in respuesta.content.decode ()

	def test_fragmento_no_incluye_campo_nombre (self):
		"""GET /tablero/fragmento/ no expone el nombre del paciente en la respuesta."""
		paciente = PacienteFactory (nombre='NombreSecreto')
		SesionFactory (paciente=paciente, oculto=False)
		cliente = Client ()

		respuesta = cliente.get (reverse ('tablero-fragmento'))

		assert 'NombreSecreto' not in respuesta.content.decode ()


@pytest.mark.django_db
class TestGestionVista:
	"""Tests para la vista de gestión protegida."""

	def test_gestion_redirige_a_login_sin_sesion (self):
		"""GET /gestion/ sin sesión activa redirige a /login/."""
		cliente = Client ()

		respuesta = cliente.get (reverse ('gestion'))

		assert respuesta.status_code == 302
		assert respuesta ['Location'] == reverse ('login')


@pytest.mark.django_db
class TestLoginVista:
	"""Tests para la vista de login."""

	def test_login_con_dominio_no_autorizado_retorna_error (self):
		"""POST /login/ con email de dominio no autorizado retorna HTTP 200 con mensaje de error."""
		cliente = Client ()

		respuesta = cliente.post (reverse ('login'), {'email': 'usuario@dominionoautorizado.com'})

		assert respuesta.status_code == 200
		assert 'no autorizado' in respuesta.content.decode ().lower ()
