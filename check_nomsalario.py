import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'NOMSAL%'")
    for r in cursor.fetchall():
        print(f"Table: {r[0]}")
    
    print("\nListing NOMSALARIO if it exists:")
    try:
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NOMSALARIO'")
        cols = [c[0] for c in cursor.fetchall()]
        print(", ".join(cols))
        
        cursor.execute("SELECT TOP 1 * FROM NOMSALARIO")
        print(cursor.fetchone())
    except:
        print("NOMSALARIO does not exist or failed.")
