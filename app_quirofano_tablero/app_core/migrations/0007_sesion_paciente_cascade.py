import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
	"""Cambia on_delete de Sesion.paciente de PROTECT a CASCADE."""

	dependencies = [
		('app_core', '0005_eliminar_registroestado'),
		('app_core', '0006_alter_sesion_paciente'),
	]

	operations = [
		migrations.AlterField (
			model_name='sesion',
			name='paciente',
			field=models.ForeignKey (on_delete=django.db.models.deletion.CASCADE, to='app_core.paciente'),
		),
	]
