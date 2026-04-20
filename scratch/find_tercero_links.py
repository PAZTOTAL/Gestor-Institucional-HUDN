from django.db import connections

def find_links(target_oid):
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME IN ('GENTERCER', 'TERCERO', 'OID_TERCERO', 'TERCERO_OID')")
        columns = cursor.fetchall()
        
        links = []
        for table, col in columns:
            try:
                cursor.execute(f"SELECT TOP 1 * FROM {table} WHERE {col} = %s", [target_oid])
                row = cursor.fetchone()
                if row:
                    links.append((table, col, row))
            except:
                pass
        return links

if __name__ == "__main__":
    oid = 259209
    results = find_links(oid)
    for r in results:
        print(f"Match in {r[0]}.{r[1]}")
        # Try to find a column in r[0] that might be a GENUSUARIO OID or name
        # ...
