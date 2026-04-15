import pymysql

SRC_CONFIG = {
    'host': '179.1.196.50',
    'port': 25469,
    'user': 'webmaster',
    'password': '24010242',
    'database': 'defenjur2'
}

TABLE = 'derechos_peticion'
FOLDERS = ['1075', '1090', '2344', '2489', '2522', '2577', '2797', '2798', '2838', '2941']

def find_folders():
    conn = pymysql.connect(**SRC_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute(f"DESCRIBE {TABLE}")
        fields = [f['Field'] for f in cursor.fetchall()]
        
        for folder in FOLDERS:
            # Search across all fields
            found = False
            for field in fields:
                cursor.execute(f"SELECT id FROM {TABLE} WHERE CAST({field} AS CHAR) LIKE %s", (f"%{folder}%",))
                row = cursor.fetchone()
                if row:
                    print(f"Match: Folder {folder} -> Field '{field}' (ID: {row['id']})")
                    found = True
                    break
            if not found:
                print(f"No match for {folder}")
    finally:
        conn.close()

find_folders()
