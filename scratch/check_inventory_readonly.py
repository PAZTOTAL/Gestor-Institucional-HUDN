import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def check_tables():
    # Test 'readonly' connection
    with connections['readonly'].cursor() as cursor:
        tables_to_check = ['INNDOCUME', 'GENUSUARIO']
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT TOP 1 * FROM {table}")
                print(f"Readonly - Table {table}: OK")
            except Exception as e:
                print(f"Readonly - Table {table}: ERROR - {e}")

if __name__ == "__main__":
    check_tables()
