import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    doc = '59829584'
    print(f"Searching for {doc} (Clara Luz) in NOMEMPLEADO:")
    cursor.execute("SELECT EMPCODIGO, EMPNOMBRE1 FROM NOMEMPLEADO WHERE EMPCODIGO LIKE %s", [f'%{doc}%'])
    print(cursor.fetchall())

    print(f"\nSearching for {doc} (Clara Luz) in NMEMPLEA:")
    cursor.execute("SELECT NEMCODIGO, NEMNOMCOM FROM NMEMPLEA WHERE NEMCODIGO LIKE %s", [f'%{doc}%'])
    print(cursor.fetchall())
