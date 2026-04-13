import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from consultas_externas.models import Hcninterr
from django.db.models import Count

def test_query():
    print("Iniciando inspección de Glasgow en el Hospital...")
    try:
        # Ver qué valores existen en el campo Glasgow
        stats = Hcninterr.objects.values('hciglasgow').annotate(total=Count('oid')).order_by('-total')[:20]
        print("Distribución de valores en hciglasgow:")
        for s in stats:
            print(f" - Valor: [{s['hciglasgow']}], Total: {s['total']}")
            
    except Exception as e:
        print(f"Error en la consulta: {e}")

if __name__ == "__main__":
    test_query()
