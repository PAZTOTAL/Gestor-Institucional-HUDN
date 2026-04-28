import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("--- REVISANDO FECHAS MÁS RECIENTES ---")
        
        cursor.execute("SELECT GETDATE()")
        print(f"Fecha/Hora actual en SQL Server: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT TOP 1 HCFECFOL FROM HCNFOLIO ORDER BY OID DESC")
        print(f"HCNFOLIO (Última fecha): {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT TOP 1 HCETFECHAING FROM HCNTCENTURED ORDER BY OID DESC")
        res = cursor.fetchone()
        print(f"HCNTCENTURED (Última fecha): {res[0] if res else 'Ninguna'}")
        
        cursor.execute("SELECT TOP 1 HCTFECTRI FROM HCNTRIAGE ORDER BY OID DESC")
        res = cursor.fetchone()
        print(f"HCNTRIAGE (Última fecha): {res[0] if res else 'Ninguna'}")

if __name__ == "__main__":
    run()
