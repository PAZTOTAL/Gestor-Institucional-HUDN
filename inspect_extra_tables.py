import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Checking NMJORASI (Jornada Asignada):")
    try:
        cursor.execute("SELECT TOP 5 * FROM NMJORASI")
        for row in cursor.fetchall():
            print(row)
    except Exception as e: print(e)

    print("\nChecking NMVINCUL again with MORE rows:")
    try:
        cursor.execute("SELECT * FROM NMVINCUL")
        for row in cursor.fetchall():
            print(row)
    except Exception as e: print(e)
