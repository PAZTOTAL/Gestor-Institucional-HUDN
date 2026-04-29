import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from defenjur_py.legal.models import CatalogoDerechoVulnerado

DERECHOS = [
    'Derecho a la Vida',
    'Derecho a la Salud',
    'Derecho de Petición',
    'Debido Proceso',
    'Mínimo Vital',
    'Dignidad Humana',
    'Seguridad Social',
    'Igualdad',
    'Libre Desarrollo de la Personalidad',
    'Trabajo',
    'Otros (Especificar)'
]

for d in DERECHOS:
    CatalogoDerechoVulnerado.objects.get_or_create(nombre=d)

print("CatalogoDerechoVulnerado populated successfully!")
