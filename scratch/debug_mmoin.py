import os
import sys
import django

# Añadir el directorio actual al path para que encuentre HospitalManagement
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'HCCMMOIN%'")
        tabs = [r[0] for r in cursor.fetchall()]
        print(f"TABLES: {tabs}")
        
        for tab in tabs:
            try:
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tab}'")
                cols = [r[0] for r in cursor.fetchall()]
                print(f"COLUMNS FOR {tab}: {cols}")
                
                cursor.execute(f"SELECT TOP 1 * FROM {tab}")
                rows = cursor.fetchall()
                print(f"SAMPLE ROW FOR {tab}: {rows}")
            except Exception as e:
                print(f"Error checking {tab}: {e}")

if __name__ == "__main__":
    run()
