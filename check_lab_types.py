import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Counts in NOMINFOLAB by ILTIPEMRES:")
    cursor.execute("SELECT ILTIPEMRES, COUNT(*) FROM NOMINFOLAB GROUP BY ILTIPEMRES")
    for r in cursor.fetchall():
        print(r)
    
    # Check if there is a table for these types
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'NOMTIP%'")
    for r in cursor.fetchall():
        print(f"Table: {r[0]}")
