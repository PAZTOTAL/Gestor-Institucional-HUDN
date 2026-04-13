import os

import pyodbc


def _bool_env(name, default):
    return os.getenv(name, default).strip().lower() == "true"


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "1433")),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", ""),
    "encrypt": _bool_env("DB_ENCRYPT", "false"),
    "trust_server_certificate": _bool_env("DB_TRUST_SERVER_CERTIFICATE", "true"),
    "connection_timeout": int(os.getenv("DB_CONNECTION_TIMEOUT_MS", "30000")) // 1000,
}


def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={DB_CONFIG['host']},{DB_CONFIG['port']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['user']};"
        f"PWD={DB_CONFIG['password']};"
        f"Encrypt={'yes' if DB_CONFIG['encrypt'] else 'no'};"
        f"TrustServerCertificate={'yes' if DB_CONFIG['trust_server_certificate'] else 'no'};"
    )
    return pyodbc.connect(conn_str, timeout=DB_CONFIG["connection_timeout"])
