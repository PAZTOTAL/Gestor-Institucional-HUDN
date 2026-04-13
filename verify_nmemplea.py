import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.apps import apps
Nmemplea = apps.get_model('consultas_externas', 'Nmemplea')

try:
    count = Nmemplea.objects.using('readonly').filter(nemestado=1).count()
    print(f"Total active employees: {count}")
    
    # Try to get one to see if fields map correctly
    if count > 0:
        emp = Nmemplea.objects.using('readonly').filter(nemestado=1).first()
        print(f"First employee found: {emp.nemcodigo}")
except Exception as e:
    print(f"Error: {e}")
