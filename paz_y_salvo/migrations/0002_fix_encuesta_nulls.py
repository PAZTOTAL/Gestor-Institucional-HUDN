from django.db import migrations, models

_CALIF_FIELDS = [
    'calif_compañeros',
    'calif_formacion',
    'calif_ambiente',
    'calif_reconocimiento',
    'calif_carga_trabajo',
    'calif_superior',
    'calif_beneficios',
    'calif_salario',
    'calif_valores',
    'calif_cultura',
    'calif_trabajo_equipo',
]

_CALIF_CHOICES = [('excelente', 'Excelente'), ('buena', 'Buena'), ('mala', 'Mala')]

# Limpia NULLs existentes en cada campo antes de aplicar NOT NULL
_clear_nulls = '; '.join(
    f"UPDATE pys_encuestas_retiro SET [{f}] = '' WHERE [{f}] IS NULL"
    for f in _CALIF_FIELDS
)


class Migration(migrations.Migration):

    dependencies = [
        ('paz_y_salvo', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=_clear_nulls,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ] + [
        migrations.AlterField(
            model_name='encuestaretiro',
            name=field,
            field=models.CharField(
                choices=_CALIF_CHOICES,
                default='',
                max_length=15,
            ),
        )
        for field in _CALIF_FIELDS
    ]
