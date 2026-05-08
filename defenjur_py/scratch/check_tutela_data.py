import os
import django
import sys

# Setup django
sys.path.append(os.path.dirname(os.getcwd()))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'defenjur_py.core.settings')
django.setup()

from legal.models import AccionTutela

# Get the last tutela
t = AccionTutela.objects.last()
if t:
    print(f"ID: {t.id}")
    print(f"Num Proceso: {t.num_proceso}")
    print(f"Fecha Llegada: {t.fecha_llegada}")
    print(f"Accionante: {t.accionante}")
    print(f"Abogado: {t.abogado_responsable}")
    print(f"Despacho: {t.despacho_judicial}")
else:
    print("No tutelas found")
