import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'HCNTCENTURED'")
        cols = [r[0] for r in cursor.fetchall()]
        print(f"COLUMNS: {cols}")
        
        cursor.execute("SELECT TOP 5 * FROM HCNTCENTURED")
        rows = cursor.fetchall()
        print(f"ROWS: {rows}")

if __name__ == "__main__":
    run()
