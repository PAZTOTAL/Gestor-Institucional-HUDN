import os
import django
import sys
from pathlib import Path

# Setup django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from certificados_laborales.services.contract_repository import get_grouped_contracts_by_cedula

def test():
    cedula = "12985653" 
    try:
        data = get_grouped_contracts_by_cedula(cedula)
        print(f"SUCCESS: Data found for {cedula}")
        print(f"Nombre: {data['nombre']}")
        print(f"Contratos: {len(data['contratos'])}")
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test()
