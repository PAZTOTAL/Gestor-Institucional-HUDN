import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    doc = '12985653'
    print(f"Searching for {doc} in GENTERCER:")
    cursor.execute("SELECT OID, TERNUMDOC, TERPRINOM, TERPRIAPE FROM GENTERCER WHERE TERNUMDOC LIKE %s", [f'%{doc}%'])
    for r in cursor.fetchall():
        print(r)

    print(f"\nSearching for {doc} in NMEMPLEA again with partial match:")
    cursor.execute("SELECT NEMCODIGO, NEMNOMCOM, NEMESTADO, NEMTIPCON FROM NMEMPLEA WHERE NEMCODIGO LIKE %s", [f'%{doc}%'])
    for r in cursor.fetchall():
        print(r)

    print("\nLooking at ANY employee with NEMESTADO != 1 but name containing '12985653' or name containing 'SISTEMAS'?")
    # No, I don't know the name.
