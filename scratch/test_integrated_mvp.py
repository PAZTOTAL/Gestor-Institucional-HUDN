import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from certificados_laborales.services.contract_repository import get_grouped_contracts_by_cedula
from certificados_laborales.services.certificate_service import generate_certificate

def test_integration():
    cedula = "19325625" # Use a known working cedula from previous tests
    print(f"Testing CEDULA: {cedula}")
    
    try:
        # 1. Test Repository
        print("Testing Repository...")
        result = get_grouped_contracts_by_cedula(cedula)
        print("Repository Result Keys:", result.keys())
        print("Nombre:", result.get('nombre'))
        print("Contratos found:", len(result.get('contratos', [])))
        
        # 2. Test Certificate Generation
        print("\nTesting Certificate Generation...")
        result['genero'] = 'masculino'
        output, filename = generate_certificate(result, 'masculino')
        print(f"Generated File: {filename}")
        print(f"Output Size: {output.getbuffer().nbytes} bytes")
        
    except Exception as e:
        import traceback
        print("\nERROR DETECTED:")
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()
