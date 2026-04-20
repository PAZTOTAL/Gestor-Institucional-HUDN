from django.db import connections

def find_links(user_oid):
    with connections['readonly'].cursor() as cursor:
        cursor.execute("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME IN ('GENUSUARIO', 'USUARIO', 'OID_USUARIO')")
        columns = cursor.fetchall()
        
        links = []
        for table, col in columns:
            try:
                # Check if user_oid exists in this table/column
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} = %s", [user_oid])
                count = cursor.fetchone()[0]
                if count > 0:
                    links.append((table, col, count))
            except:
                pass
        return links

if __name__ == "__main__":
    # Alexander's OID is 2379
    results = find_links(2379)
    for r in results:
        print(f"Table: {r[0]}, Col: {r[1]}, Rows: {r[2]}")
