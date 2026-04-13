import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Distinct NEMTIPCON (Tipo Contrato) for active:")
    cursor.execute("SELECT NEMTIPCON, COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1 GROUP BY NEMTIPCON")
    for r in cursor.fetchall():
        print(r)

    print("\nDistinct NEMCLAEMP (Clase Empleado) for active:")
    cursor.execute("SELECT NEMCLAEMP, COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1 GROUP BY NEMCLAEMP")
    for r in cursor.fetchall():
        print(r)

    print("\nDistinct NEMSETOR (Sector?) for active:")
    cursor.execute("SELECT NEMSETOR, COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1 GROUP BY NEMSETOR")
    for r in cursor.fetchall():
        print(r)
