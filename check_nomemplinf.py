import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'NOMEMPLINF'")
    if cursor.fetchone():
        print("NOMEMPLINF exists!")
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NOMEMPLINF'")
        print([c[0] for c in cursor.fetchall()])
    else:
        print("NOMEMPLINF does not exist.")
