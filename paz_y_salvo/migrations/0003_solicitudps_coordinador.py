from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paz_y_salvo', '0002_fix_encuesta_nulls'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudps',
            name='coordinador',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
