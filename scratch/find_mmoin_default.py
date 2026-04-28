import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['default'].cursor() as cursor:
        print("Searching for tables in 'default' database containing 'mmoin'...")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE UPPER(TABLE_NAME) LIKE '%MMOIN%'")
        tabs = [r[0] for r in cursor.fetchall()]
        print(f"MMOIN Tables (default): {tabs}")

if __name__ == "__main__":
    run()
