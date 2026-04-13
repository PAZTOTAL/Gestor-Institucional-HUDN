import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Columns in CTNCENCOS:")
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'CTNCENCOS'")
    for c in cursor.fetchall():
        print(f"- {c[0]}")

    print("\nSample from CTNCENCOS:")
    cursor.execute("SELECT TOP 10 * FROM CTNCENCOS")
    for r in cursor.fetchall():
        print(r)
