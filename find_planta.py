import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.apps import apps
Nmemplea = apps.get_model('consultas_externas', 'Nmemplea')

print("Checking if any active employee has 'PLANTA' in their data:")
# We'll check common char fields
chars = ['nemnomcom', 'nemapelli', 'nemnombre', 'nemresolu', 'njacodigo', 'nemclagra']
for char in chars:
    count = Nmemplea.objects.using('readonly').filter(nemestado=1).filter(**{f"{char}__icontains": "PLANTA"}).count()
    if count > 0:
        print(f"- Field '{char}' has {count} matches for 'PLANTA'")

# Also check Nmvincul
Nmvincul = apps.get_model('consultas_externas', 'Nmvincul')
count = Nmvincul.objects.using('readonly').filter(nvinombre__icontains="PLANTA").count()
print(f"Nmvincul has {count} matches for 'PLANTA' in nvinombre")

# Also check Nomvincula
Nomvincula = apps.get_model('consultas_externas', 'Nomvincula')
count = Nomvincula.objects.using('readonly').filter(vinnombre__icontains="PLANTA").count()
print(f"Nomvincula has {count} matches for 'PLANTA' in vinnombre")
