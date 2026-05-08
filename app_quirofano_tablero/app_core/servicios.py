import logging

from .models import EstadoQuirurgico, Paciente, Sesion

logger = logging.getLogger (__name__)


coloresEstado = {
	EstadoQuirurgico.EN_PREPARACION:  'bg-yellow-400',
	EstadoQuirurgico.EN_CIRUGIA:      'bg-orange-500',
	EstadoQuirurgico.EN_RECUPERACION: 'bg-blue-500',
	EstadoQuirurgico.FINALIZADO:      'bg-gray-400',
	EstadoQuirurgico.OTRO:            'bg-purple-500',
}


class SesionServicio:
	"""Gestiona la creación y actualización de sesiones quirúrgicas."""

	def aplicarEstado (self, paciente: Paciente, nuevoEstado: str, labelOtro: str = 'Otro') -> Sesion:
		"""Crea la sesión si no existe, o actualiza el estado si ya existe."""
		sesion, creada = Sesion.objects.get_or_create (
			paciente=paciente,
			oculto=False,
			defaults={'estado': nuevoEstado, 'labelOtro': labelOtro},
		)

		if not creada:
			sesion.estado = nuevoEstado
			if nuevoEstado == EstadoQuirurgico.OTRO:
				sesion.labelOtro = labelOtro

		if nuevoEstado == EstadoQuirurgico.FINALIZADO:
			sesion.oculto = True

		sesion.save ()

		logger.info (f"Estado aplicado: {paciente.identificacion} → {nuevoEstado}")
		return sesion


def obtenerSesionesVisibles ():
	"""Retorna sesiones activas no ocultas, ordenadas por actualizadoEn descendente."""
	return (
		Sesion.objects
		.filter (oculto=False)
		.select_related ('paciente')
		.only ('id', 'paciente__identificacion', 'estado', 'labelOtro', 'ingresadoEn', 'actualizadoEn')
		.order_by ('-actualizadoEn')
	)
