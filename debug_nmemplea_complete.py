import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    doc = '12985653'
    print(f"Searching for {doc} in ALL of NMEMPLEA (ignoring state):")
    cursor.execute("SELECT NEMCODIGO, NEMNOMCOM, NEMESTADO, NEMTIPCON, NEMCLAEMP FROM NMEMPLEA WHERE NEMCODIGO LIKE %s", [f'%{doc}%'])
    for r in cursor.fetchall():
        print(r)
    
    # Try searching by name too
    print(f"\nSearching for 'ALEXANDER' in NMEMPLEA:")
    cursor.execute("SELECT NEMCODIGO, NEMNOMCOM, NEMESTADO FROM NMEMPLEA WHERE NEMNOMCOM LIKE '%ALEXANDER%'")
    for r in cursor.fetchall():
        print(r)
