import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from consultas_externas.models import Hcnsigvit
from django.db.models import Count

def test_query():
    print("Analizando tipos de signos vitales (Hcnsigvit)...")
    try:
        stats = Hcnsigvit.objects.values('hcntipsvit').annotate(total=Count('oid')).order_by('-total')[:20]
        for s in stats:
            print(f" - Tipo: {s['hcntipsvit']}, Total: {s['total']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_query()
