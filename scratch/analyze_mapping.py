import pymysql

# Known FTP folders from previous listing:
# /web/defenjur_files/acciones_tutela: 1330, 1398, 1399, 1400
# /web/defenjur_files/derechos_peticion: ... 3555

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
        # Get first few records to see available fields
        cursor.execute(f"DESCRIBE {table}")
        fields = [f['Field'] for f in cursor.fetchall()]
        print(f"Fields: {fields}")
        
        for folder in folder_samples:
            print(f"Searching for record corresponding to folder: {folder}")
            # Search in all text/int fields
            for field in fields:
                cursor.execute(f"SELECT * FROM {table} WHERE CAST({field} AS CHAR) = %s", (folder,))
                row = cursor.fetchone()
                if row:
                    print(f"  MATCH FOUND! Folder '{folder}' matches field '{field}'")
                    # return field
        
    finally:
        conn.close()

analyze_mapping('acciones_tutela', ['1330', '1398'])
analyze_mapping('derechos_peticion', ['3555'])
analyze_mapping('procs_judiciales_pasiva', []) # Need samples later
