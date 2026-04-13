import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    doc = '12985653'
    print(f"Searching for {doc} in NOMEMPLEADO by EMPCODIGO:")
    try:
        cursor.execute("SELECT EMPCODIGO, EMPNOMBRE1, EMPNOMBRE2, EMPAPELLI1, EMPAPELLI2 FROM NOMEMPLEADO WHERE EMPCODIGO LIKE %s", [f'%{doc}%'])
        res = cursor.fetchall()
        for r in res:
            print(r)
    except Exception as e:
        print(e)
    
    print("\nCounting records in NOMEMPLEADO:")
    cursor.execute("SELECT COUNT(*) FROM NOMEMPLEADO")
    print(cursor.fetchone()[0])
