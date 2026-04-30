import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def check_columns():
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT TOP 1 * FROM INNDOCUME")
        columns = [col[0] for col in cursor.description]
        print(f"Columns: {columns}")

if __name__ == "__main__":
    check_columns()
