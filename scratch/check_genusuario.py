from django.db import connections
with connections['readonly'].cursor() as cursor:
    cursor.execute("SELECT TOP 0 * FROM GENUSUARIO")
    print([column[0] for column in cursor.description])
