import pymysql

SRC_CONFIG = {
    'host': '179.1.196.50',
    'port': 25469,
    'user': 'webmaster',
    'password': '24010242',
    'database': 'defenjur2'
}

TABLE_FOLDERS = {
    'acciones_tutela': ['1901', '2185', '1331'],
    'derechos_peticion': ['102', '3555', '3500']
}

def global_search():
    conn = pymysql.connect(**SRC_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        for table, folders in TABLE_FOLDERS.items():
            print(f"\n--- Searching in {table} ---")
            cursor.execute(f"DESCRIBE {table}")
            fields = [f['Field'] for f in cursor.fetchall()]
            
            for folder in folders:
                found = False
                for field in fields:
                    cursor.execute(f"SELECT id FROM {table} WHERE CAST({field} AS CHAR) LIKE %s", (f"%{folder}%",))
                    row = cursor.fetchone()
                    if row:
                        print(f"  MATCH: Folder '{folder}' found in Field '{field}' (Record ID: {row['id']})")
                        found = True
                        break
                if not found:
                    print(f"  NOT FOUND: Folder {folder}")
        
    finally:
        conn.close()

global_search()
