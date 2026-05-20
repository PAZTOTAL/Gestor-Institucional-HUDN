# Formularios de la aplicación crue_traslados.

import datetime

from django import forms

from .models import Traslado


# ─── Tailwind CSS classes reutilizables ──────────────────────────────────────

_CLASES_INPUT = (
	'w-full border border-gray-300 rounded-md px-3 py-2 text-sm '
	'focus:outline-none focus:ring-2 focus:ring-blue-500'
)


# ─── Widget personalizado fecha + hora separados ─────────────────────────────

class WidgetFechaHoraSeparados (forms.SplitDateTimeWidget):
	"""Widget que renderiza fecha y hora como dos inputs separados con estilos Tailwind."""

	def __init__ (self, attrs=None):
		"""Inicializa los sub-widgets de fecha (type=date) y hora (type=text, HH:MM)."""
		widgetsFechaHora = [
			forms.DateInput (format='%Y-%m-%d', attrs={
				'type': 'date',
				'class': _CLASES_INPUT,
			}),
			forms.TimeInput (format='%H:%M', attrs={
				'type': 'text',
				'placeholder': 'HH:MM',
				'pattern': '[0-2][0-9]:[0-5][0-9]',
				'maxlength': '5',
				'class': _CLASES_INPUT,
			}),
		]
		# Llamar al __init__ de MultiWidget directamente, pasando los sub-widgets
		forms.MultiWidget.__init__ (self, widgets=widgetsFechaHora, attrs=attrs)

	def decompress (self, value):
		"""Descompone un datetime en [fecha, hora] para los sub-widgets."""
		if value:
			from django.utils import timezone
			if hasattr (value, 'tzinfo') and value.tzinfo is not None:
				value = timezone.localtime (value)
			if hasattr (value, 'date') and hasattr (value, 'time'):
				return [value.date (), value.time ()]
			return [value, None]
		return [None, None]


# ─── Campo SplitDateTimeField que acepta hora vacía ──────────────────────────

class CampoFechaHoraOpcional (forms.SplitDateTimeField):
	"""SplitDateTimeField que usa 00:00 cuando el componente de hora está vacío."""

	def clean (self, value):
		"""Si la hora está vacía pero hay fecha, combina la fecha con 00:00."""
		# value es una lista [fecha_str, hora_str] proveniente del SplitDateTimeWidget
		if isinstance (value, (list, tuple)) and len (value) == 2:
			fechaStr = value [0]
			horaStr = value [1]
			if fechaStr and (not horaStr or not str (horaStr).strip ()):
				# Fecha presente pero hora vacía: usar 00:00
				value = [fechaStr, '00:00']
			elif not fechaStr:
				# Sin fecha: retornar None
				return None
		return super ().clean (value)


# ─── Formulario principal de traslado ────────────────────────────────────────

class FormularioTraslado (forms.ModelForm):
	"""Formulario para crear y editar registros de Traslado."""

	# ── Campos explícitos con SplitDateTimeField + widget personalizado ───
	fecha_reporte = forms.SplitDateTimeField (
		required=True,
		widget=WidgetFechaHoraSeparados (),
		label='Fecha Reporte',
	)
	fecha_egreso = CampoFechaHoraOpcional (
		required=False,
		widget=WidgetFechaHoraSeparados (),
		label='Fecha Egreso',
	)
	fecha_ingreso = CampoFechaHoraOpcional (
		required=False,
		widget=WidgetFechaHoraSeparados (),
		label='Fecha Ingreso',
	)

	class Meta:
		model = Traslado
		fields = [
			'fecha_reporte',
			'fecha_egreso',
			'fecha_ingreso',
			'nombre_paciente',
			'documento',
			'servicio',
			'quien_reporta',
			'destino',
			'procedimiento',
			'medico',
			'aux_enfermeria',
			'conductor',
			'radio_operador',
			'ambulancia',
			'observacion',
		]
		widgets = {
			'nombre_paciente': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 255,
				}
			),
			'documento': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 50,
				}
			),
			'servicio': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 100,
				}
			),
			'quien_reporta': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 100,
				}
			),
			'destino': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 100,
				}
			),
			'procedimiento': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 255,
				}
			),
			'medico': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 100,
				}
			),
			'aux_enfermeria': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 100,
				}
			),
			'conductor': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 100,
				}
			),
			'radio_operador': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 100,
				}
			),
			'ambulancia': forms.TextInput (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'maxlength': 100,
				}
			),
			'observacion': forms.Textarea (
				attrs={
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
					'rows': 3,
				}
			),
		}
		labels = {
			'fecha_reporte': 'Fecha Reporte',
			'fecha_egreso': 'Fecha Egreso',
			'fecha_ingreso': 'Fecha Ingreso',
			'nombre_paciente': 'Nombre de Paciente',
			'documento': 'Documento',
			'servicio': 'Servicio',
			'quien_reporta': 'Quien Reporta',
			'destino': 'Destino',
			'procedimiento': 'Procedimiento',
			'medico': 'Médico',
			'aux_enfermeria': 'Aux. Enfermería',
			'conductor': 'Conductor',
			'radio_operador': 'Radio Operador',
			'ambulancia': 'Ambulancia de Traslado',
			'observacion': 'Observación',
		}

	def __init__ (self, *args, **kwargs):
		"""Inicializa el formulario con valores por defecto de fecha, hora y radio_operador."""
		self.usuario = kwargs.pop ('usuario', None)
		super ().__init__ (*args, **kwargs)

		# Agregar uppercase a todos los inputs de texto
		for nombre, campo in self.fields.items ():
			if hasattr (campo, 'widget') and hasattr (campo.widget, 'attrs'):
				if isinstance (campo.widget, (forms.TextInput, forms.Textarea)):
					campo.widget.attrs ['style'] = campo.widget.attrs.get ('style', '') + 'text-transform: uppercase;'

		# Radio operador: auto-llenado con el usuario actual para registros nuevos
		if self.usuario:
			if self.instance is None or not self.instance.pk:
				self.initial ['radio_operador'] = self.usuario.username

		# Solo precargar valores por defecto para registros nuevos (sin instancia existente)
		if self.instance is None or not self.instance.pk:
			hoyISO = datetime.date.today ().isoformat ()
			horaActual = datetime.datetime.now ().strftime ('%H:%M')

			self.initial ['fecha_reporte'] = [hoyISO, horaActual]
			self.initial ['fecha_egreso'] = ['', '']
			self.initial ['fecha_ingreso'] = ['', '']

	def clean_fecha_egreso (self):
		"""Retorna None si el componente de hora está vacío."""
		return self.cleaned_data.get ('fecha_egreso')

	def clean_fecha_ingreso (self):
		"""Retorna None si el componente de hora está vacío."""
		return self.cleaned_data.get ('fecha_ingreso')

	def clean_radio_operador (self):
		"""Retorna el valor ingresado por el usuario."""
		return self.cleaned_data.get ('radio_operador', '')

	def clean (self):
		"""Convierte todos los campos de texto a mayúsculas."""
		datos = super ().clean ()
		for nombre, valor in datos.items ():
			if isinstance (valor, str):
				datos [nombre] = valor.upper ()
		return datos


# ─── Formulario de cambio de contraseña ──────────────────────────────────────

class FormularioCambiarContrasena (forms.Form):
	"""Formulario para que el usuario autenticado cambie su propia contraseña."""

	contrasena_actual = forms.CharField (
		label='Contraseña actual',
		widget=forms.PasswordInput (attrs={
			'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'autocomplete': 'current-password',
		}),
	)
	nueva_contrasena = forms.CharField (
		label='Nueva contraseña',
		widget=forms.PasswordInput (attrs={
			'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'autocomplete': 'new-password',
		}),
	)
	confirmar_contrasena = forms.CharField (
		label='Confirmar nueva contraseña',
		widget=forms.PasswordInput (attrs={
			'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'autocomplete': 'new-password',
		}),
	)

	def clean (self):
		"""Valida que la nueva contraseña y su confirmación coincidan."""
		datos = super ().clean ()
		nuevaContrasena = datos.get ('nueva_contrasena')
		confirmarContrasena = datos.get ('confirmar_contrasena')

		if nuevaContrasena and confirmarContrasena and nuevaContrasena != confirmarContrasena:
			raise forms.ValidationError ('La nueva contraseña y su confirmación no coinciden.')

		return datos
