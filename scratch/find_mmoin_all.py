import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("Listing ALL tables and filtering for 'mmoin' in Python...")
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES")
        all_tabs = [r[0] for r in cursor.fetchall()]
        matches = [t for t in all_tabs if 'mmoin' in t.lower()]
        print(f"Matches for 'mmoin': {matches}")
        
        if not matches:
            print("No 'mmoin' matches. Searching for 'mmo'...")
            matches_mmo = [t for t in all_tabs if 'mmo' in t.lower()]
            print(f"Matches for 'mmo': {matches_mmo[:20]}... (Total: {len(matches_mmo)})")

if __name__ == "__main__":
    run()
