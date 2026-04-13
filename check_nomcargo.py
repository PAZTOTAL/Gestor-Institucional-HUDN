import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'NOMCAR%'")
    for r in cursor.fetchall():
        print(f"Table: {r[0]}")
    
    print("\nListing NOMCARGO if it exists:")
    try:
        cursor.execute("SELECT * FROM NOMCARGO")
        for r in cursor.fetchall():
            print(r)
    except:
        print("NOMCARGO does not exist.")
