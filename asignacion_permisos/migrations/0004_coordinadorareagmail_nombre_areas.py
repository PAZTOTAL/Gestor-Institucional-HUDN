from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asignacion_permisos', '0003_coordinadorareagmail'),
    ]

    operations = [
        migrations.AddField(
            model_name='coordinadorareagmail',
            name='nombre',
            field=models.CharField(default='', max_length=150),
        ),
        migrations.AddField(
            model_name='coordinadorareagmail',
            name='areas',
            field=models.TextField(default=''),
        ),
        migrations.AlterModelOptions(
            name='coordinadorareagmail',
            options={'ordering': ['nombre']},
        ),
    ]
