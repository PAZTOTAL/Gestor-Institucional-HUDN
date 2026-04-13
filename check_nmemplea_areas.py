import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Sample from NMEMPLEA (Area fields):")
    cursor.execute("SELECT TOP 10 NEMCODIGO, NEMNOMCOM, GASCODIGO, NEMTIPARE FROM NMEMPLEA WHERE NEMESTADO = 1")
    rows = cursor.fetchall()
    for r in rows:
        print(r)

    print("\nDistinct GASCODIGO in active employees:")
    cursor.execute("SELECT DISTINCT GASCODIGO FROM NMEMPLEA WHERE NEMESTADO = 1")
    for r in cursor.fetchall():
        print(r)
