import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Listing NOMGRUPO table:")
    try:
        cursor.execute("SELECT * FROM NOMGRUPO")
        for r in cursor.fetchall():
            print(r)
    except:
        print("NOMGRUPO table does not exist.")

    print("\nListing NOMSUBGRU table:")
    try:
        cursor.execute("SELECT * FROM NOMSUBGRU")
        for r in cursor.fetchall():
            print(r)
    except:
        print("NOMSUBGRU table does not exist.")
