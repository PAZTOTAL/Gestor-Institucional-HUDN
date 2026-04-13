import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

with connections['readonly'].cursor() as cursor:
    print("Checking 'NOM' tables for Alex Pantoja:")
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'NOM%'")
    tables = [t[0] for t in cursor.fetchall()]
    for t in tables:
        try:
            # Check if table has a column that looks like doc or name
            cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}' AND (COLUMN_NAME LIKE '%DOC%' OR COLUMN_NAME LIKE '%NOM%')")
            cols = cursor.fetchall()
            if cols:
                col_name = cols[0][0]
                cursor.execute(f"SELECT TOP 1 * FROM {t} WHERE {col_name} LIKE '%12985653%'")
                res = cursor.fetchone()
                if res:
                    print(f"FOUND IN {t}: {res}")
        except:
            pass
