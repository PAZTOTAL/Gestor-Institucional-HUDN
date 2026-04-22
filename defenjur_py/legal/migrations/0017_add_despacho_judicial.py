# Generated manually - add DespachoJudicial model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legal', '0016_remove_acciontutela_area_responsable_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DespachoJudicial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ciudad', models.CharField(max_length=100, verbose_name='Ciudad')),
                ('nombre', models.CharField(max_length=255, verbose_name='Nombre del Despacho')),
                ('correo', models.EmailField(blank=True, max_length=255, null=True, verbose_name='Correo Institucional')),
            ],
            options={
                'verbose_name': 'Despacho Judicial',
                'verbose_name_plural': 'Despachos Judiciales',
                'db_table': 'defenjur_app_despachojudicial',
                'ordering': ['ciudad', 'nombre'],
            },
        ),
    ]
