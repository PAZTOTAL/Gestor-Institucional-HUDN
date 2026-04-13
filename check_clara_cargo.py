import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT * FROM NOMCARGO WHERE OID = 320")
    print(f"Cargo 320: {cursor.fetchone()}")
