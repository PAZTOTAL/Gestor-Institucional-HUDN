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
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE UPPER(TABLE_NAME) LIKE '%IN24%' OR UPPER(TABLE_NAME) LIKE '%MMO%'")
            tables = [r[0] for r in cursor.fetchall()]
            print(f"Tablas encontradas: {tables}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
