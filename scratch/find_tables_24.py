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
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE UPPER(TABLE_NAME) LIKE '%24%'")
            tables = [r[0] for r in cursor.fetchall()]
            print(f"Tablas con 24 encontradas: {tables}")
            
            cursor.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE UPPER(COLUMN_NAME) LIKE '%MMOIN%' OR UPPER(COLUMN_NAME) LIKE '%IN24%'")
            cols = [r for r in cursor.fetchall()]
            print(f"Columnas encontradas: {cols}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
