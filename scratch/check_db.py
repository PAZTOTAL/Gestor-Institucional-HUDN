import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def check_columns():
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT TOP 0 * FROM GENUSUARIO")
        columns = [column[0] for column in cursor.description]
        print("Columns in GENUSUARIO:", columns)

if __name__ == "__main__":
    check_columns()
