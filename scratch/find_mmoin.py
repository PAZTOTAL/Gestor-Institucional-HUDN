import os
import sys
import django

# Add current directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("Searching for tables containing 'MMOIN'...")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%MMOIN%'")
        tabs = [r[0] for r in cursor.fetchall()]
        print(f"Found Tables: {tabs}")
        
        for tab in tabs:
            print(f"\n--- Structure for {tab} ---")
            cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tab}'")
            cols = cursor.fetchall()
            for col in cols:
                print(f"  {col[0]} ({col[1]})")
            
            print(f"Sampling 1 row from {tab}:")
            cursor.execute(f"SELECT TOP 1 * FROM {tab}")
            row = cursor.fetchone()
            print(f"  {row}")

if __name__ == "__main__":
    run()
