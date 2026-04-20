from django.db import connections

def search_value(val):
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME LIKE 'GEN%' OR TABLE_NAME LIKE 'PSN%' OR TABLE_NAME LIKE 'NOM%'")
        columns = cursor.fetchall()
        
        found = []
        for table, col, dtype in columns:
            if dtype in ('int', 'bigint', 'decimal', 'numeric'):
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = %s", [val])
                    if cursor.fetchone()[0] > 0:
                        found.append((table, col))
                except:
                    pass
        return found

if __name__ == "__main__":
    v = 259209 # Alexander's GENTERCER OID
    res = search_value(v)
    for r in res:
        print(f"Match in {r[0]}.{r[1]}")
