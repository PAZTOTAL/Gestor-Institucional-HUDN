from django.db import connections

def list_tables_columns():
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT TOP 1 * FROM HPNSUBGRU")
        columns = [col[0] for col in cursor.description]
        print(f"HPNSUBGRU columns: {columns}")
        
        cursor.execute("SELECT TOP 1 * FROM HPNGRUPOS")
        columns = [col[0] for col in cursor.description]
        print(f"HPNGRUPOS columns: {columns}")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
    django.setup()
    list_tables_columns()
