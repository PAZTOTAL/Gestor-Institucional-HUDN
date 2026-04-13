import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.apps import apps
Nmemplea = apps.get_model('consultas_externas', 'Nmemplea')

print("Counts by NEMCLAEMP (Active only):")
for val in [0, 3]:
    count = Nmemplea.objects.using('readonly').filter(nemestado=1, nemclaemp=val).count()
    print(f"- {val}: {count}")

print("\nCounts by NEMTIPCON (Active only):")
count = Nmemplea.objects.using('readonly').filter(nemestado=1, nemtipcon=1).count()
print(f"- 1: {count}")
