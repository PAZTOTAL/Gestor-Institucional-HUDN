import os
import sys
import django

sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    try:
        cursor.execute("SELECT TOP 5 carpeta FROM defenjur_app_acciontutela")
        rows = cursor.fetchall()
        print("Data in 'carpeta' column:")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
