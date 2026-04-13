import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Checking job titles for NEMCLAEMP = 0:")
    query = """
        SELECT TOP 10 
            e.NEMNOMCOM, c.NCENOMBRE, e.NEMCLAEMP
        FROM NMEMPLEA e
        LEFT JOIN NMCARGOS c ON RTRIM(LTRIM(e.NJACODIGO)) = RTRIM(LTRIM(c.NCECODIGO))
        WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 0
    """
    cursor.execute(query)
    for r in cursor.fetchall():
        print(r)

    print("\nChecking job titles for NEMCLAEMP = 3:")
    query = """
        SELECT TOP 10 
            e.NEMNOMCOM, c.NCENOMBRE, e.NEMCLAEMP
        FROM NMEMPLEA e
        LEFT JOIN NMCARGOS c ON RTRIM(LTRIM(e.NJACODIGO)) = RTRIM(LTRIM(c.NCECODIGO))
        WHERE e.NEMESTADO = 1 AND e.NEMCLAEMP = 3
    """
    cursor.execute(query)
    for r in cursor.fetchall():
        print(r)
