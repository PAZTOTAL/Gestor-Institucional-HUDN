import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from consultas_externas.models import Hcninterr

def test_query():
    print("Inspeccionando registros de Hcninterr...")
    try:
        regs = Hcninterr.objects.all().order_by('-oid')[:5]
        for r in regs:
            print("--- Registro ---")
            for field in r._meta.fields:
                val = getattr(r, field.name)
                if val and val != 0:
                    print(f"{field.name}: {val}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_query()
