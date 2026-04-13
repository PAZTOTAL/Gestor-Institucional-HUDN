import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Searching for 'PANTOJA' in NMEMPLEA:")
    cursor.execute("SELECT NEMCODIGO, NEMNOMCOM, NEMESTADO, NEMTIPCON FROM NMEMPLEA WHERE NEMNOMCOM LIKE '%PANTOJA%'")
    for r in cursor.fetchall():
        print(r)
