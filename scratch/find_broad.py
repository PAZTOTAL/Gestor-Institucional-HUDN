import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("Searching for any table with 'mmoin' (case insensitive)...")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE UPPER(TABLE_NAME) LIKE '%MMOIN%'")
        tabs = [r[0] for r in cursor.fetchall()]
        print(f"MMOIN Tables: {tabs}")
        
        print("\nSearching for any table with 'GLASGOW' column...")
        cursor.execute("SELECT DISTINCT TABLE_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE UPPER(COLUMN_NAME) LIKE '%GLASGOW%'")
        glas_tabs = [r[0] for r in cursor.fetchall()]
        print(f"Glasgow Tables: {glas_tabs}")

if __name__ == "__main__":
    run()
