import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    doc = '59829584'
    cursor.execute("SELECT NCECODIGO, NJACODIGO, GASCODIGO FROM NMEMPLEA WHERE NEMCODIGO LIKE %s", [f'%{doc}%'])
    print(f"Clara in NMEMPLEA: {cursor.fetchone()}")
