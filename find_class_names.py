import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%CLAEMP%' OR TABLE_NAME LIKE '%CLANOM%'")
    tables = cursor.fetchall()
    print("Potential Class Tables:")
    for t in tables:
        print(f"- {t[0]}")

    print("\nChecking NMCLAEMP if it exists:")
    try:
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NMCLAEMP'")
        for c in cursor.fetchall():
            print(f"- {c[0]}")
        
        print("\nValues in NMCLAEMP:")
        cursor.execute("SELECT * FROM NMCLAEMP")
        for r in cursor.fetchall():
            print(r)
    except:
        print("NMCLAEMP not found.")

    print("\nChecking GENCLAEMP if it exists:")
    try:
        cursor.execute("SELECT * FROM GENCLAEMP")
        for r in cursor.fetchall():
            print(r)
    except:
        print("GENCLAEMP not found.")
