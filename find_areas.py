import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    # Look for tables that might represent Areas or Cost Centers
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%AREA%' OR TABLE_NAME LIKE '%CENATE%' OR TABLE_NAME LIKE '%COSTOS%' OR TABLE_NAME LIKE '%CC% '")
    tables = cursor.fetchall()
    print("Potential Area/Cost Center Tables:")
    for t in tables:
        print(f"- {t[0]}")

    # Also check NMEMPLEA columns for common area/cost center prefixes
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NMEMPLEA' AND (COLUMN_NAME LIKE '%ARE%' OR COLUMN_NAME LIKE '%CEN%' OR COLUMN_NAME LIKE '%CCE%')")
    cols = cursor.fetchall()
    print("\nPotential Area Columns in NMEMPLEA:")
    for c in cols:
        print(f"- {c[0]}")
