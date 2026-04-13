import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Contents of NOMPLARES (possibly Planta de Personal):")
    try:
        cursor.execute("SELECT * FROM NOMPLARES")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error: {e}")

    print("\nContents of NOMACTADM (Administrative Acts):")
    try:
        cursor.execute("SELECT * FROM NOMACTADM")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error: {e}")
