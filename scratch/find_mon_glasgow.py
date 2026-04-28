import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE UPPER(TABLE_NAME) LIKE 'HC%MON%'")
            tables = [r[0] for r in cursor.fetchall()]
            print(f"Tablas HC*MON*: {tables}")
            
            for tab in tables:
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tab}' AND UPPER(COLUMN_NAME) LIKE '%GLAS%'")
                cols = [r[0] for r in cursor.fetchall()]
                if cols:
                    print(f"  -> {tab} tiene GLASGOW: {cols}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
