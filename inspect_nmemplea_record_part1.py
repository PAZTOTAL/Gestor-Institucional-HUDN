import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT TOP 1 * FROM NMEMPLEA WHERE NEMESTADO = 1")
    row = cursor.fetchone()
    cols = [col[0] for col in cursor.description]
    print("--- 0 to 45 ---")
    for i in range(0, 45):
        print(f"{i:3}: {cols[i]}: {row[i]}")
