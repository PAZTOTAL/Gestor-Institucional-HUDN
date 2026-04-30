import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def check_users():
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM GENUSUARIO")
        count = cursor.fetchone()[0]
        print(f"GENUSUARIO count: {count}")

if __name__ == "__main__":
    check_users()
