from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asignacion_permisos', '0007_add_firma_imagen_coordinador'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudapc',
            name='empresa_tercerizada_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
