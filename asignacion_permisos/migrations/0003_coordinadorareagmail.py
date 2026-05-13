from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asignacion_permisos', '0002_encabezadoconfig_texto_mensaje_campoconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoordinadorAreaGmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coordinador_id', models.IntegerField(unique=True)),
                ('gmail', models.CharField(blank=True, default='', max_length=150)),
            ],
            options={
                'db_table': 'apc_coordinador_area_gmail',
            },
        ),
    ]
