import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("Checking HCNCTATEMED columns...")
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'HCNCTATEMED'")
        cols = [r[0] for r in cursor.fetchall()]
        print(f"Columns: {cols}")
        
        print("\nSampling 5 rows from HCNCTATEMED with Glasgow values...")
        cursor.execute("SELECT TOP 5 HCCGLAS1, HCCGLAS2 FROM HCNCTATEMED WHERE HCCGLAS1 IS NOT NULL OR HCCGLAS2 IS NOT NULL")
        rows = cursor.fetchall()
        for r in rows:
            print(f" - {r}")

if __name__ == "__main__":
    run()
