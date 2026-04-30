import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def check_count():
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM INNDOCUME")
        count = cursor.fetchone()[0]
        print(f"INNDOCUME count: {count}")

if __name__ == "__main__":
    check_count()
