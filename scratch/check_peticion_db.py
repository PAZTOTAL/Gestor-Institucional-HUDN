import os
import sys
import django

sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from defenjur_py.legal.models import DerechoPeticion
from django.db import connection

model = DerechoPeticion
table_name = model._meta.db_table

with connection.cursor() as cursor:
    try:
        cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
        columns = [col[0] for col in cursor.description]
        print(f"Columns in {table_name}:")
        print(columns)
    except Exception as e:
        print(f"Error accessing table {table_name}: {e}")
