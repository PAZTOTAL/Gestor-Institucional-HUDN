import logging

from django.conf import settings

logger = logging.getLogger (__name__)


class NotificacionServicio:
	"""Gestiona notificaciones internas y envío de SMS via Twilio."""

	def notificarCambioEstado (self, paciente, nuevoEstado: str) -> None:
		"""Registra el cambio de estado en log y envía SMS si el paciente tiene teléfono."""
		logger.info (f"[NOTIFICACION] Paciente {paciente.identificacion}: nuevo estado → {nuevoEstado}")
		self._enviarSms (paciente, nuevoEstado)

	def _enviarSms (self, paciente, nuevoEstado: str) -> None:
		"""Envía SMS al teléfono del paciente si está registrado. No bloquea ante fallos."""
		print ('[SMS] Enviando SMS...', paciente.telefono)
		if not paciente.telefono:
			return

		try:
			from twilio.rest import Client

			account_sid = getattr (settings, 'TWILIO_ACCOUNT_SID', '')
			auth_token  = getattr (settings, 'TWILIO_AUTH_TOKEN', '')
			from_number = getattr (settings, 'TWILIO_FROM_NUMBER', '')

			if not all ([account_sid, auth_token, from_number]):
				print ('[SMS] Credenciales Twilio no configuradas. SMS no enviado.')
				logger.warning ('[SMS] Credenciales Twilio no configuradas. SMS no enviado.')
				return

			from datetime import datetime
			nombre  = paciente.nombre or paciente.identificacion
			destino = f"+57{paciente.telefono}"
			hora    = datetime.now ().strftime ('%I:%M %p').lower ().lstrip ('0')
			mensaje = f"Quiroinfo: Paciente {nombre} pasa a: {nuevoEstado.replace ('EN_','')}. Hora: {hora}"

			Client (account_sid, auth_token).messages.create (
				body=mensaje,
				from_=from_number,
				to=destino,
			)
			logger.info (f"[SMS] Enviado a {destino}: {mensaje}")

		except Exception as e:
			print (f"[SMS] Error al enviar SMS a {paciente.telefono}: {e}")
			logger.error (f"[SMS] Error al enviar SMS a {paciente.telefono}: {e}")
