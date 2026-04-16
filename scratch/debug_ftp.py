import ftplib
import os

host = '172.20.100.25'
user = 'contratacion_admin'
pwd = 'contratacionHUDN*01122025'

try:
    print(f"Connecting to {host}...")
    ftp = ftplib.FTP(host, timeout=10)
    print("Login...")
    ftp.login(user, pwd)
    print("Listing /...")
    print(ftp.nlst('/'))
    print("Listing /defenjur_files...")
    print(ftp.nlst('/defenjur_files'))
    ftp.quit()
    print("Success")
except Exception as e:
    print(f"Failed: {e}")
