import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    ids = ['12985653', '59829584']
    for doc in ids:
        print(f"\nChecking record for DOCUMENT: {doc}")
        # Search for the document, handling potential leading zeros
        query = "SELECT NEMCODIGO, NEMNOMCOM, NEMTIPCON, NEMCLAEMP, NEMESTADO, GASCODIGO FROM NMEMPLEA WHERE NEMCODIGO LIKE %s"
        cursor.execute(query, [f'%{doc}%'])
        rows = cursor.fetchall()
        if not rows:
            print("No record found in NMEMPLEA.")
        for r in rows:
            print(r)

    print("\nCounting ALL active employees in NMEMPLEA:")
    cursor.execute("SELECT COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1")
    print(f"Total Active: {cursor.fetchone()[0]}")

    print("\nCounting all distinct NEMTIPCON and NEMCLAEMP for ACTIVE staff:")
    cursor.execute("SELECT NEMTIPCON, NEMCLAEMP, COUNT(*) FROM NMEMPLEA WHERE NEMESTADO = 1 GROUP BY NEMTIPCON, NEMCLAEMP")
    for r in cursor.fetchall():
        print(r)
