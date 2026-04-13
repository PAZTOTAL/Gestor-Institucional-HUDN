import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Checking for NMCARGO table:")
    try:
        cursor.execute("SELECT TOP 5 * FROM NMCARGO")
        for r in cursor.fetchall():
            print(r)
    except:
        print("NMCARGO not found.")

    print("\nChecking for NMCARGOS table:")
    try:
        cursor.execute("SELECT TOP 5 * FROM NMCARGOS")
        for r in cursor.fetchall():
            print(r)
    except:
        print("NMCARGOS not found.")
