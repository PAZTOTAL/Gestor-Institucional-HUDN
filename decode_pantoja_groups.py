import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT * FROM NOMSUBGRU WHERE OID = 21")
    print(f"Subgrupo 21: {cursor.fetchone()}")
    
    cursor.execute("SELECT * FROM NOMGRUPO WHERE OID = 1")
    print(f"Grupo 1: {cursor.fetchone()}")
