from django.db import connections

def inspect_db():
    with connections['readonly'].cursor() as cursor:
        # Check tables
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'NM%'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        # Check tables with AREA
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%%AREA%%'")
        area_tables = [t[0] for t in cursor.fetchall()]
        print(f"Area Tables: {area_tables}")

if __name__ == '__main__':
    inspect_db()
