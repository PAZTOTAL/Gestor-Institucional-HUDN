from django.db import migrations


class Migration(migrations.Migration):
	"""Elimina la columna descripcion_otro de la tabla sesiones."""

	dependencies = [
		('app_core', '0001_initial'),
	]

	operations = [
		migrations.RemoveField(
			model_name='sesion',
			name='descripcionOtro',
		),
	]
