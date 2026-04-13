import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Counts in NOMINFOLAB by ILTIPOVINC:")
    cursor.execute("SELECT ILTIPOVINC, COUNT(*) FROM NOMINFOLAB GROUP BY ILTIPOVINC")
    for r in cursor.fetchall():
        # Let's try to find names for these types too if there is a table
        print(r)
