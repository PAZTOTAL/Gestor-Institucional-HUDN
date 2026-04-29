# Formularios de la aplicación traslados.

from django import forms
from django.contrib.auth import get_user_model

from .models import TrasladoPaciente

Usuario = get_user_model ()


class FormularioTraslado (forms.ModelForm):
	"""Formulario para crear y editar registros de TrasladoPaciente."""

	class Meta:
		model = TrasladoPaciente
		fields = [
			'fecha',
			'hora_reporte',
			'hora_egreso',
			'hora_ingreso',
			'nombre_paciente',
			'documento',
			'servicio',
			'quien_reporta',
			'destino',
			'procedimiento',
			'medico',
			'conductor',
			'radio_operador',
			'ambulancia',
			'observacion',
		]
		widgets = {
			'fecha': forms.DateInput (
				format='%Y-%m-%d',
				attrs={
					'type': 'date',
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
				}
			),
			'hora_reporte': forms.TimeInput (
				format='%H:%M',
				attrs={
					'type': 'text',
					'placeholder': 'HH:MM',
					'pattern': '[0-2][0-9]:[0-5][0-9]',
					'maxlength': '5',
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
				}
			),
			'hora_egreso': forms.TimeInput (
				format='%H:%M',
				attrs={
					'type': 'text',
					'placeholder': 'HH:MM',
					'pattern': '[0-2][0-9]:[0-5][0-9]',
					'maxlength': '5',
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
				}
			),
			'hora_ingreso': forms.TimeInput (
				format='%H:%M',
				attrs={
					'type': 'text',
					'placeholder': 'HH:MM',
					'pattern': '[0-2][0-9]:[0-5][0-9]',
					'maxlength': '5',
					'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
				}
			),
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
			'fecha': 'Fecha',
			'hora_reporte': 'Hora Reporte',
			'hora_egreso': 'Hora de Egreso',
			'hora_ingreso': 'Hora de Ingreso',
			'nombre_paciente': 'Nombre de Paciente',
			'documento': 'Documento',
			'servicio': 'Servicio',
			'quien_reporta': 'Quien Reporta',
			'destino': 'Destino',
			'procedimiento': 'Procedimiento',
			'medico': 'Médico',
			'conductor': 'Conductor',
			'radio_operador': 'Radio Operador',
			'ambulancia': 'Ambulancia de Traslado',
			'observacion': 'Observación',
		}


class FormularioCrearUsuario (forms.Form):
	"""Formulario para crear un nuevo usuario con username, contraseña inicial y rol."""

	username = forms.CharField (
		label='Nombre de usuario',
		max_length=150,
		widget=forms.TextInput (attrs={
			'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'autocomplete': 'off',
		}),
	)
	password = forms.CharField (
		label='Contraseña inicial',
		widget=forms.PasswordInput (attrs={
			'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'autocomplete': 'new-password',
		}),
	)
	rol = forms.ChoiceField (
		label='Rol',
		choices=Usuario.ROL_CHOICES,
		widget=forms.Select (attrs={
			'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
		}),
	)


class FormularioCambiarContrasenaPropia (forms.Form):
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


class FormularioCambiarContrasenaUsuario (forms.Form):
	"""Formulario para que el DIRECTOR cambie la contraseña de otro usuario."""

	nueva_contrasena = forms.CharField (
		label='Nueva contraseña',
		widget=forms.PasswordInput (attrs={
			'class': 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'autocomplete': 'new-password',
		}),
	)
	confirmar_contrasena = forms.CharField (
		label='Confirmar contraseña',
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
