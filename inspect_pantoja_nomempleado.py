import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    doc = '12985653'
    print(f"Checking NOMEMPLEADO details for {doc}:")
    cursor.execute("SELECT * FROM NOMEMPLEADO WHERE EMPCODIGO = %s", [doc])
    row = cursor.fetchone()
    cols = [col[0] for col in cursor.description]
    for c, v in zip(cols, row):
        print(f"{c}: {v}")
