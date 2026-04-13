import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from consultas_externas.models import Hcninterr
from django.db.models import Max

def test_query():
    print("Iniciando búsqueda de valores > 0 en Glasgow...")
    try:
        max_val = Hcninterr.objects.aggregate(Max('hciglasgow'))
        print(f"Máximo valor de Glasgow encontrado: {max_val}")
        
        count_valid = Hcninterr.objects.filter(hciglasgow__gt=0).count()
        print(f"Total registros con Glasgow > 0: {count_valid}")
        
    except Exception as e:
        print(f"Error en la consulta: {e}")

if __name__ == "__main__":
    test_query()
