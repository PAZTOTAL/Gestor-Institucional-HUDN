import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connection

def check_tables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sys.tables WHERE name LIKE 'defenjur_app_%'")
        tables = cursor.fetchall()
        print("Existing defenjur_app tables:")
        for t in tables:
            print(t[0])

if __name__ == "__main__":
    check_tables()
