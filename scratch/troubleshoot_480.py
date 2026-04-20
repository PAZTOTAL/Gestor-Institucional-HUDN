import pymysql
import ftplib
import os

SRC_CONFIG = {
    'host': '179.1.196.50',
    'port': 25469,
    'user': 'webmaster',
    'password': '24010242',
    'database': 'defenjur2'
}

def troubleshoot_480():
    print("--- Troubleshooting record 480 ---")
    conn = pymysql.connect(**SRC_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("SELECT * FROM acciones_tutela WHERE id=480")
        record = cursor.fetchone()
        if not record:
            print("Record 480 not found in MySQL!")
            return
        
        print(f"Record 480 details: {record}")
        
        # Get all folders in NAS for tutelas
        ftp = ftplib.FTP('172.20.100.25')
        ftp.login('contratacion_admin', 'contratacionHUDN*01122025')
        folders = [os.path.basename(f) for f in ftp.nlst('/web/defenjur_files/acciones_tutela')]
        ftp.quit()
        
        print(f"Total folders in acciones_tutela: {len(folders)}")
        
        # Check if any value in the record matches any folder
        for folder in folders:
            for field, value in record.items():
                if value and str(folder) in str(value):
                    print(f"  POTENTIAL MATCH: Folder '{folder}' found in field '{field}' (Value: {value})")
                elif value and str(value) in str(folder):
                   print(f"  POTENTIAL REVERSE MATCH: Field '{field}' (Value: {value}) found in folder name '{folder}'")

    finally:
        conn.close()

troubleshoot_480()
