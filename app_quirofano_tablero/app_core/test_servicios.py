import pytest
import factory
from datetime import timezone
from hypothesis import given, settings
from hypothesis import strategies as st

from .models import EstadoQuirurgico, Paciente, Sesion
from .servicios import SesionServicio, obtenerSesionesVisibles


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

class PacienteFactory (factory.django.DjangoModelFactory):
	"""Factory para crear instancias de Paciente en tests."""

	class Meta:
		model = Paciente

	identificacion = factory.Sequence (lambda n: f"PAC-{n:04d}")
	nombre         = factory.Sequence (lambda n: f"Paciente {n}")
	origen         = 'PROGRAMADO'


class SesionFactory (factory.django.DjangoModelFactory):
	"""Factory para crear instancias de Sesion en tests."""

	class Meta:
		model = Sesion

	paciente = factory.SubFactory (PacienteFactory)
	estado   = EstadoQuirurgico.EN_PREPARACION
	oculto   = False


# ---------------------------------------------------------------------------
# Tests de SesionServicio.aplicarEstado
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAplicarEstado:
	"""Tests unitarios para SesionServicio.aplicarEstado."""

	def setup_method (self):
		"""Inicializa el servicio antes de cada test."""
		self.servicio = SesionServicio ()

	def test_crea_sesion_nueva_si_no_existe (self):
		"""aplicarEstado() crea una sesión nueva cuando el paciente no tiene sesión activa."""
		paciente = PacienteFactory ()

		sesion = self.servicio.aplicarEstado (paciente, EstadoQuirurgico.EN_PREPARACION)

		assert Sesion.objects.filter (paciente=paciente, oculto=False).count () == 1
		assert sesion.estado == EstadoQuirurgico.EN_PREPARACION
		assert sesion.paciente == paciente

	def test_actualiza_estado_si_sesion_ya_existe (self):
		"""aplicarEstado() actualiza el estado cuando el paciente ya tiene sesión activa."""
		paciente = PacienteFactory ()
		SesionFactory (paciente=paciente, estado=EstadoQuirurgico.EN_PREPARACION)

		sesion = self.servicio.aplicarEstado (paciente, EstadoQuirurgico.EN_CIRUGIA)

		assert sesion.estado == EstadoQuirurgico.EN_CIRUGIA
		assert Sesion.objects.filter (paciente=paciente, oculto=False).count () == 1

	def test_finalizado_marca_oculto_true (self):
		"""aplicarEstado() con FINALIZADO marca oculto=True y conserva el registro en BD."""
		paciente = PacienteFactory ()
		SesionFactory (paciente=paciente, estado=EstadoQuirurgico.EN_CIRUGIA)

		sesion = self.servicio.aplicarEstado (paciente, EstadoQuirurgico.FINALIZADO)

		sesion.refresh_from_db ()
		assert sesion.oculto is True
		assert Sesion.objects.filter (paciente=paciente).exists ()

	def test_otro_sin_descripcion_no_lanza_error (self):
		"""aplicarEstado() con OTRO y sin descripción retorna sesión sin error."""
		paciente = PacienteFactory ()

		sesion = self.servicio.aplicarEstado (paciente, EstadoQuirurgico.OTRO)

		assert sesion.estado == EstadoQuirurgico.OTRO


# ---------------------------------------------------------------------------
# Tests de obtenerSesionesVisibles
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestObtenerSesionesVisibles:
	"""Tests unitarios para obtenerSesionesVisibles."""

	def test_no_retorna_sesiones_ocultas (self):
		"""obtenerSesionesVisibles() no incluye sesiones con oculto=True."""
		SesionFactory (oculto=True)
		SesionFactory (oculto=False)

		resultado = list (obtenerSesionesVisibles ())

		assert len (resultado) == 1
		assert resultado [0].oculto is False

	def test_retorna_sesiones_ordenadas_por_actualizado_en_descendente (self):
		"""obtenerSesionesVisibles() retorna sesiones ordenadas por actualizadoEn descendente."""
		sesion1 = SesionFactory ()
		sesion2 = SesionFactory ()
		sesion3 = SesionFactory ()

		resultado = list (obtenerSesionesVisibles ())
		ids       = [s.id for s in resultado]

		assert ids == [sesion3.id, sesion2.id, sesion1.id]

	# **Validates: Requirements 3.1**
	@given (st.lists (st.booleans (), min_size=1))
	@settings (max_examples=100)
	@pytest.mark.django_db
	def test_solo_retorna_sesiones_visibles (self, listaOculto):
		"""Propiedad 1: obtenerSesionesVisibles() retorna exactamente las sesiones con oculto=False."""
		sesionesCreadas = []
		for valorOculto in listaOculto:
			sesion = SesionFactory (oculto=valorOculto)
			sesionesCreadas.append (sesion)

		idsVisiblesEsperados = {s.id for s in sesionesCreadas if not s.oculto}
		resultado            = list (obtenerSesionesVisibles ())
		idsResultado         = {s.id for s in resultado}

		assert idsResultado == idsVisiblesEsperados

		for sesion in sesionesCreadas:
			sesion.delete ()
		for sesion in sesionesCreadas:
			sesion.paciente.delete ()

	# **Validates: Requirements 3.2, 4.1**
	@given (st.lists (st.datetimes (timezones=st.just (timezone.utc)), min_size=2))
	@settings (max_examples=100)
	@pytest.mark.django_db
	def test_sesiones_ordenadas_por_actualizado_en_descendente (self, fechas):
		"""Propiedad 2: obtenerSesionesVisibles() retorna sesiones ordenadas por actualizadoEn descendente."""
		sesionesCreadas = []
		for fecha in fechas:
			sesion = SesionFactory (oculto=False)
			Sesion.objects.filter (id=sesion.id).update (actualizadoEn=fecha)
			sesion.refresh_from_db ()
			sesionesCreadas.append (sesion)

		resultado = list (obtenerSesionesVisibles ())

		for i in range (len (resultado) - 1):
			assert resultado [i].actualizadoEn >= resultado [i + 1].actualizadoEn

		for sesion in sesionesCreadas:
			sesion.delete ()
		for sesion in sesionesCreadas:
			sesion.paciente.delete ()
