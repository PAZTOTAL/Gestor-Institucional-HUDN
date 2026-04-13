import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    docs = {'12985653': 'Alexander', '59829584': 'Clara'}
    for doc, name in docs.items():
        print(f"\n--- {name} ({doc}) ---")
        cursor.execute("SELECT NOMINFOLAB FROM NOMEMPLEADO WHERE EMPCODIGO LIKE %s", [f'%{doc}%'])
        info_oid = cursor.fetchone()[0]
        
        cursor.execute(f"SELECT * FROM NOMINFOLAB WHERE OID = {info_oid}")
        row = cursor.fetchone()
        cols = [col[0] for col in cursor.description]
        for c, v in zip(cols, row):
            if v != 0 and v is not None and v != '' and v != False:
                print(f"{c}: {v}")
