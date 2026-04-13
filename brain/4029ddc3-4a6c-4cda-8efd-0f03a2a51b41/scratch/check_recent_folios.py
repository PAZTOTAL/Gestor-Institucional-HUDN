import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from consultas_externas.models import Hcnfolio
from django.db.models import Max

def test_query():
    print("Iniciando búsqueda de folios recientes...")
    try:
        max_fec = Hcnfolio.objects.aggregate(Max('hcfecfol'))
        print(f"Fecha del folio más reciente: {max_fec}")
        
    except Exception as e:
        print(f"Error en la consulta: {e}")

if __name__ == "__main__":
    test_query()
