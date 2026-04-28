import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("Searching for tables starting with 'HCC'...")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'HCC%'")
        tabs = [r[0] for r in cursor.fetchall()]
        print(f"HCC Tables: {tabs}")
        
        print("\nSearching for tables containing 'MOIN'...")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%MOIN%'")
        tabs_moin = [r[0] for r in cursor.fetchall()]
        print(f"MOIN Tables: {tabs_moin}")

if __name__ == "__main__":
    run()
