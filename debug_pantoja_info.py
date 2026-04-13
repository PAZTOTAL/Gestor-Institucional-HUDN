import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Checking NOMINFOLAB schema:")
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NOMINFOLAB'")
    cols = [c[0] for c in cursor.fetchall()]
    print(", ".join(cols))

    print("\nSample from NOMINFOLAB for Alexander Pantoja:")
    # First get his NOMINFOLAB OID from NOMEMPLEADO
    cursor.execute("SELECT NOMINFOLAB FROM NOMEMPLEADO WHERE EMPCODIGO = '12985653'")
    info_oid = cursor.fetchone()[0]
    print(f"Info OID: {info_oid}")
    
    cursor.execute(f"SELECT * FROM NOMINFOLAB WHERE OID = {info_oid}")
    print(cursor.fetchone())
