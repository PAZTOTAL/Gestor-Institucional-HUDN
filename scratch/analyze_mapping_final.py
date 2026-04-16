import pymysql

SRC_CONFIG = {
    'host': '179.1.196.50',
    'port': 25469,
    'user': 'webmaster',
    'password': '24010242',
    'database': 'defenjur2'
}

def analyze_mapping(table, folder_samples):
    print(f"\n--- Analyzing {table} ---")
    conn = pymysql.connect(**SRC_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute(f"DESCRIBE {table}")
        fields = [f['Field'] for f in cursor.fetchall()]
        
        for folder in folder_samples:
            print(f"Searching for folder: {folder}")
            found = False
            for field in fields:
                cursor.execute(f"SELECT id, num_proceso FROM {table} WHERE CAST({field} AS CHAR) = %s", (folder,))
                row = cursor.fetchone()
                if row:
                    print(f"  MATCH: Field '{field}' (ID: {row['id']})")
                    found = True
                    break
            if not found:
                print(f"  NO MATCH for {folder}")
    finally:
        conn.close()

# Sampless from FTP
analyze_mapping('acciones_tutela', ['479', '787', '791', '1330', '2815'])
analyze_mapping('derechos_peticion', ['3555', '3500'])
