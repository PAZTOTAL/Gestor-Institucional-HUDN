import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM NOMCARGO")
    print(f"Total NOMCARGO: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT TOP 5 * FROM NOMCARGO")
    for r in cursor.fetchall():
        print(r)
