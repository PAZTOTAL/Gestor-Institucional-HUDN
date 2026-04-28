import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        ALTER TABLE defenjur_app_acciontutela DROP COLUMN termino_dias_horas;
    """)
    cursor.execute("""
        ALTER TABLE defenjur_app_acciontutela ADD 
        termino_dias INT NULL,
        termino_horas INT NULL;
    """)
    print("Columns adjusted successfully.")
