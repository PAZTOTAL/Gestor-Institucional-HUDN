# Migration 0018 — Add audit fields to AccionTutela

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legal', '0017_add_despacho_judicial'),
    ]

    operations = [
        migrations.AddField(
            model_name='acciontutela',
            name='fecha_registro',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Fecha de registro'),
        ),
        migrations.AddField(
            model_name='acciontutela',
            name='usuario_carga',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Usuario que cargó'),
        ),
    ]
