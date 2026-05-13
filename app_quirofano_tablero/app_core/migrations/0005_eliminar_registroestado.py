from django.db import migrations


class Migration(migrations.Migration):
	"""Elimina el modelo RegistroEstado y su tabla registro_estados."""

	dependencies = [
		('app_core', '0003_sesion_labelotro'),
		('app_core', '0004_alter_sesion_paciente'),
	]

	operations = [
		migrations.DeleteModel (
			name='RegistroEstado',
		),
	]
