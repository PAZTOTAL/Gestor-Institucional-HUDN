import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Sample cargos for NEMCLAEMP = 3:")
    query = """
        SELECT TOP 10 
            e.NEMCODIGO, e.NEMNOMCOM, c.NMCNOM, e.NEMCLAEMP
        FROM NMEMPLEA e
        LEFT JOIN NMCARGOS c ON RTRIM(LTRIM(e.NMRCODIGO)) = RTRIM(LTRIM(c.NMCCOD))
        WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 3
    """
    cursor.execute(query)
    for r in cursor.fetchall():
        print(r)

    print("\nSample cargos for NEMCLAEMP = 0:")
    query = """
        SELECT TOP 10 
            e.NEMCODIGO, e.NEMNOMCOM, c.NMCNOM, e.NEMCLAEMP
        FROM NMEMPLEA e
        LEFT JOIN NMCARGOS c ON RTRIM(LTRIM(e.NMRCODIGO)) = RTRIM(LTRIM(c.NMCCOD))
        WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 0
    """
    cursor.execute(query)
    for r in cursor.fetchall():
        print(r)
