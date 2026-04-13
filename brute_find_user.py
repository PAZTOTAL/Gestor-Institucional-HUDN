import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Listing ALL tables again (searching for Alex Pantoja '12985653'):")
    # I'll search for '12985653' in any table that looks like it has employee data
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'NM%' OR TABLE_NAME LIKE 'NOM%' OR TABLE_NAME LIKE 'GEN%'")
    tables = [t[0] for t in cursor.fetchall()]
    
    found = False
    for t in tables:
        try:
            cursor.execute(f"SELECT TOP 1 * FROM {t} WHERE CAST(CONCAT_WS(' ', *) AS VARCHAR(MAX)) LIKE '%12985653%'")
            res = cursor.fetchone()
            if res:
                print(f"MATCH IN {t}!")
                found = True
        except:
            pass
    if not found:
        print("No match found in any likely table.")
