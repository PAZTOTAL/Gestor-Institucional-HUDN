import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NMEMPLEA'")
    columns = cursor.fetchall()
    print("Columns in NMEMPLEA:")
    for col in columns:
        print(f"- {col[0]}")

    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NMVINCUL'")
    columns = cursor.fetchall()
    print("\nColumns in NMVINCUL:")
    for col in columns:
        print(f"- {col[0]}")

    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NOMVINCULA'")
    columns = cursor.fetchall()
    print("\nColumns in NOMVINCULA:")
    for col in columns:
        print(f"- {col[0]}")
