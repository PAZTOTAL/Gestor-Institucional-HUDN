import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.apps import apps
Nmemplea = apps.get_model('consultas_externas', 'Nmemplea')

print("Samples of active employees (Code, Name, NemTipCon, NemClaEmp):")
for emp in Nmemplea.objects.using('readonly').filter(nemestado=1)[:10]:
    print(f"- {emp.nemcodigo}: {emp.nemnomcom} | TC:{emp.nemtipcon} | CE:{emp.nemclaemp}")
