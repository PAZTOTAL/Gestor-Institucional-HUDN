import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Searching for tables containing 'EMPLEA':")
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%EMPLEA%'")
    for r in cursor.fetchall():
        print(r)
    
    print("\nTotal record count in NMEMPLEA:")
    cursor.execute("SELECT COUNT(*) FROM NMEMPLEA")
    print(cursor.fetchone()[0])
