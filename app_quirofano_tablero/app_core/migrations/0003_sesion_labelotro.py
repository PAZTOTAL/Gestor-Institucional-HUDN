from django.db import migrations, models


class Migration(migrations.Migration):
	"""Agrega el campo labelOtro a la tabla sesiones."""

	dependencies = [
		('app_core', '0002_remove_sesion_descripcionotro'),
	]

	operations = [
		migrations.AddField(
			model_name='sesion',
			name='labelOtro',
			field=models.CharField (max_length=50, default='Otro'),
		),
	]
