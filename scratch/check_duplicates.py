import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from usuarios.models import PerfilUsuario
from django.db.models import Count

duplicates = PerfilUsuario.objects.values('cedula').annotate(cedula_count=Count('cedula')).filter(cedula_count__gt=1)

if not duplicates:
    print("No se encontraron cédulas duplicadas en PerfilUsuario.")
else:
    print("Se encontraron las siguientes cédulas duplicadas:")
    for entry in duplicates:
        print(f"Cédula: {entry['cedula']}, Repeticiones: {entry['cedula_count']}")
        users = PerfilUsuario.objects.filter(cedula=entry['cedula'])
        for p in users:
            print(f"  - Usuario: {p.user.username}, ID: {p.user.id}")
