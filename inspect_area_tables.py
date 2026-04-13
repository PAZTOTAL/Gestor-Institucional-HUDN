import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Columns in GENTAREA:")
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'GENTAREA'")
    cols = cursor.fetchall()
    for c in cols:
        print(f"- {c[0]}")

    print("\nColumns in ADNCENATE:")
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ADNCENATE'")
    cols = cursor.fetchall()
    for c in cols:
        print(f"- {c[0]}")

    print("\nSample values from GENTAREA:")
    cursor.execute("SELECT TOP 5 * FROM GENTAREA")
    rows = cursor.fetchall()
    for r in rows:
        print(r)
