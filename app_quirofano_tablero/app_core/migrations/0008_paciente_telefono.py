from django.db import migrations, models


class Migration(migrations.Migration):
	"""Agrega el campo telefono al modelo Paciente."""

	dependencies = [
		('app_core', '0007_sesion_paciente_cascade'),
	]

	operations = [
		migrations.AddField (
			model_name='paciente',
			name='telefono',
			field=models.CharField (max_length=10, null=True, blank=True),
		),
	]
