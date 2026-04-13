import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Distinct NEMCLAEMP values:")
    cursor.execute("SELECT DISTINCT NEMCLAEMP FROM NMEMPLEA")
    for row in cursor.fetchall():
        print(f"- {row[0]}")

    print("\nDistinct NEMTIPCON values:")
    cursor.execute("SELECT DISTINCT NEMTIPCON FROM NMEMPLEA")
    for row in cursor.fetchall():
        print(f"- {row[0]}")
