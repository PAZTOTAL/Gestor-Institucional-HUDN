import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%CENCOS%' OR TABLE_NAME LIKE '%COSTOS%'")
    tables = cursor.fetchall()
    print("Potential Cost Center Tables:")
    for t in tables:
        print(f"- {t[0]}")

    print("\nChecking GENCENCOS columns if it exists:")
    try:
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'GENCENCOS'")
        for c in cursor.fetchall():
            print(f"- {c[0]}")
    except:
        print("GENCENCOS table not found.")
