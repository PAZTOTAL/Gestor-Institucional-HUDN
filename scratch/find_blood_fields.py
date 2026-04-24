from django.apps import apps
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

models = apps.get_app_config('consultas_externas').get_models()
found = []

for model in models:
    fields = [f.name for f in model._meta.fields if 'gs' in f.name.lower() or 'rh' in f.name.lower() or 'sang' in f.name.lower() or 'grupo' in f.name.lower()]
    if fields:
        found.append((model.__name__, fields))

for model_name, fields in found:
    print(f"{model_name}: {fields}")
