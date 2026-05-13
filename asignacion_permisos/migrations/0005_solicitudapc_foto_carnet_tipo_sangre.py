from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asignacion_permisos', '0004_coordinadorareagmail_nombre_areas'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudapc',
            name='foto_carnet',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='solicitudapc',
            name='tipo_sangre',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
    ]
