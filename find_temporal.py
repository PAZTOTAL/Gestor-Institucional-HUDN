import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Checking NOMVINCULA for 'TEMPORAL':")
    try:
        cursor.execute("SELECT * FROM NOMVINCULA WHERE VINNOMBRE LIKE '%TEMPORAL%'")
        for row in cursor.fetchall():
            print(row)
    except Exception as e: print(e)

    print("\nChecking NMVINCUL for 'TEMPORAL':")
    try:
        cursor.execute("SELECT * FROM NMVINCUL WHERE NMVNOM LIKE '%TEMPORAL%'")
        for row in cursor.fetchall():
            print(row)
    except Exception as e: print(e)

    print("\nAll values in NOMVINCULA:")
    try:
        cursor.execute("SELECT * FROM NOMVINCULA")
        for row in cursor.fetchall():
            print(row)
    except Exception as e: print(e)
