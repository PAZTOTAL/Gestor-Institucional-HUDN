import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    doc = '12985653' # Alexander
    cursor.execute("SELECT NOMINFOLAB FROM NOMEMPLEADO WHERE EMPCODIGO LIKE %s", [f'%{doc}%'])
    info_oid = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT * FROM NOMINFOLAB WHERE OID = {info_oid}")
    row = cursor.fetchone()
    cols = [col[0] for col in cursor.description]
    for c, v in zip(cols, row):
        print(f"{c}: {v}")
