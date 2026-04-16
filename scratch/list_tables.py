from django.db import connections
with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'GEN%' OR TABLE_NAME LIKE 'PSN%'")
    tables = [row[0] for row in cursor.fetchall()]
    print("\n".join(tables))
