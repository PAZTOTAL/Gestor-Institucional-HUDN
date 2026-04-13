import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    doc = '12985653'
    print(f"Searching for {doc} in NOMEMPLEADO:")
    try:
        # Check columns
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NOMEMPLEADO'")
        cols = [c[0] for c in cursor.fetchall()]
        print("Columns: " + ", ".join(cols))
        
        # Search
        cursor.execute(f"SELECT * FROM NOMEMPLEADO WHERE CAST(CONCAT_WS(' ', *) AS VARCHAR(MAX)) LIKE '%{doc}%'")
        res = cursor.fetchall()
        for r in res:
            print(r)
    except Exception as e:
        print(e)
