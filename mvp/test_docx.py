from certificados.services.db import get_connection
from certificados.services.contract_repository import get_grouped_contracts_by_cedula
from certificados.services.certificate_service import generate_certificate
import traceback

def test():
    c = get_connection().cursor()
    c.execute("SELECT TOP 1 CAST(cedula_nit AS VARCHAR(100)) FROM dbo.contratos_2024")
    cedula = c.fetchone()[0]
    print("Testing with CEDULA:", cedula)
    
    data = get_grouped_contracts_by_cedula(cedula)
    print("Grouped contracts found:", data['nombre'])
    
    try:
        buffer, filename = generate_certificate(data, "MASCULINO")
        print("Success! Filename:", filename)
    except Exception as e:
        traceback.print_exc()

test()
