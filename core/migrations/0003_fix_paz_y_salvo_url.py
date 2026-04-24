from django.db import migrations


def fix_paz_y_salvo_url(apps, schema_editor):
    DashboardModule = apps.get_model('core', 'DashboardModule')
    DashboardModule.objects.filter(
        url='/modulo/paz-y-salvo/'
    ).update(url='/paz-y-salvo/')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_dashboardmodule_slug'),
    ]

    operations = [
        migrations.RunPython(fix_paz_y_salvo_url, migrations.RunPython.noop),
    ]
