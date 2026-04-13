import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Contents of NMVINCUL:")
    cursor.execute("SELECT * FROM NMVINCUL")
    for row in cursor.fetchall():
        print(row)

    print("\nContents of NOMVINCULA:")
    cursor.execute("SELECT * FROM NOMVINCULA")
    for row in cursor.fetchall():
        print(row)
