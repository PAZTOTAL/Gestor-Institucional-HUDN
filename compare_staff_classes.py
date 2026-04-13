import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Sample employees with NEMCLAEMP = 3:")
    cursor.execute("SELECT TOP 5 NEMCODIGO, NEMNOMCOM, NEMCARGO, NEMCLAEMP FROM NMEMPLEA WHERE NEMESTADO = 1 AND NEMCLAEMP = 3")
    for r in cursor.fetchall():
        print(r)

    print("\nSample employees with NEMCLAEMP = 0:")
    cursor.execute("SELECT TOP 5 NEMCODIGO, NEMNOMCOM, NEMCARGO, NEMCLAEMP FROM NMEMPLEA WHERE NEMESTADO = 1 AND NEMCLAEMP = 0")
    for r in cursor.fetchall():
        print(r)
