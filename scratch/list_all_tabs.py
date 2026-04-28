import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("Listing all tables (first 500) to see naming patterns...")
        cursor.execute("SELECT TOP 500 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_NAME")
        tabs = [r[0] for r in cursor.fetchall()]
        for t in tabs:
            print(f" - {t}")

if __name__ == "__main__":
    run()
