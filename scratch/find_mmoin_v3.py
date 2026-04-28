import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("Searching for VIEWS containing 'mmoin'...")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE UPPER(TABLE_NAME) LIKE '%MMOIN%'")
        views = [r[0] for r in cursor.fetchall()]
        print(f"MMOIN Views: {views}")

        print("\nSearching for any table containing 'mmoin' (no upper filter in SQL, filter in python)...")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES")
        all_tabs = [r[0] for r in cursor.fetchall()]
        matches = [t for t in all_tabs if 'mmoin' in t.lower()]
        print(f"Matches for 'mmoin': {matches}")

if __name__ == "__main__":
    run()
