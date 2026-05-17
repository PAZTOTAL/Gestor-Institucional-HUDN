#!/usr/bin/env python3

"""
Simple DB <-> CSV migration utility.

Supported:
- PostgreSQL  -> CSV
- MySQL		  -> CSV
- MSSQL		  -> CSV
- CSV		  -> MySQL
- CSV		  -> MSSQL

Examples
--------

# Export PG table to CSV
python migrate_db.py pg_to_csv remision remision.csv

# Export MySQL table to CSV
python migrate_db.py mysql_to_csv remision remision.csv

# Export MSSQL table to CSV
python migrate_db.py mssql_to_csv remision remision.csv

# Import CSV to MySQL
python migrate_db.py csv_to_mysql remision.csv remision

# Import CSV to MSSQL
python migrate_db.py csv_to_mssql remision.csv remision

# Import CSV to POSTGRES
python migrate_db.py csv_to_pg remision.csv remision

# Import POSTGRES to MSSQL
python migrate_db.py pg_to_mssql <table name>
"""

import sys
import csv

import psycopg2
import mysql.connector
import pyodbc

from datetime import datetime
import pandas as pd

# =========================================================
# CONFIG
# =========================================================

CONFIG_PG_LOCAL = {
	"host": "localhost",
	"port": 5432,
	"database": "crue_remisiones_db",
	"user": "postgres",
	"password": "postgres2026",
}

CONFIG_PG_HUDN = {
	"host": "172.20.10.250",
	"port": 5432,
	"database": "crue_remisiones_db",
	"user": "postgres",
	"password": "postgres2026",
}


CONFIG_MSSQL_LOCAL = {
	"server": "localhost",
	"database": "GestorInstitucional",
	"user": "apantoja",
	"password": "ConsultasPantojaHUDN_2026$",
	"driver": "{ODBC Driver 17 for SQL Server}",
}

CONFIG_MSSQL_HUDN = {
	"server": "172.20.100.209",
	"database": "GestorInstitucional",
	"user": "apantoja",
	"password": "ConsultasPantojaHUDN_2026$",
	"driver": "{ODBC Driver 17 for SQL Server}",
}

CONFIG_MYSQL_LOCAL = {
	"host": "localhost",
	"port": 3306,
	"database": "GestorInstitucional",
	"user": "apantoja",
	"password": "ConsultasPantojaHUDN_2026$",
}

# =========================================================
#CONFIG_PG	  = CONFIG_PG_HUDN
CONFIG_PG	 = CONFIG_PG_HUDN
CONFIG_MSSQL = CONFIG_MSSQL_HUDN

# =========================================================
# EXPORT FUNCTIONS
# =========================================================
#-- Remove id, created_by, and, check valid dates
def getValidValues(row):
	print(f"\n+++ {row=}")

	row = row[1:-1]

	# Normalize ONLY datetime fields
	for idx in [0, -3]:
		if pd.isna(row[idx]) or row[idx] in ("NaT", ""):
			row[idx] = None

	# Truncate text safely
	if row[-7]:
		row[-7] = str(row[-7])[:300]

	# Convert Colombia time -> UTC
	if row[0] is not None:
		dt = pd.to_datetime(row[0])
		# If naive datetime, assume Colombia timezone
		if dt.tzinfo is None:
			dt = dt.tz_localize("America/Bogota")

		dt = dt.tz_convert("UTC")

		# MSSQL datetime is naive
		#dt = dt.tz_localize(None)

		row[0] = dt.to_pydatetime()

	print(f"\n>>> {row=}")

	return row

#def getValidValues (row):
#	print (f"\n+++ {row=}")
#
#	row = row[1:-1]
#
#	# Normalize ONLY datetime fields
#	if pd.isna(row[0]) or row[0] == "NaT" or row[0] == "":
#		row[0] = None
#
#	if pd.isna(row[-3]) or row[-3] == "NaT" or row[-3] == "":
#		row[-3] = None
#
#	# Truncate text safely
#	if row[-7]:
#		row[-7] = str(row[-7])[:300]
#
#	# Convert Colombia time -> UTC
#	dt = pd.to_datetime(row[0])	
#	dt = dt.tz_convert('UTC')
#	# Remove tzinfo because MSSQL datetime is naive
#	dt = dt.tz_localize(None)
#	row[0] = dt.to_pydatetime()
#
#	print (f"\n>>> {row=}")
#
#	return row

import threading
import psycopg2
import pyodbc


#-----------------------------------------------------------------------
# Robust migration: - PostgreSQL -> MSSQL
# - Skips existing records.  Continues on errors. Runs in background thread
#-----------------------------------------------------------------------
def pg_to_mssql (pg_table, mssql_table, pk_field="id", batch_size=1000):
	print (f"+++ {pg_to_mssql=}")
	
	def worker():
		print(f"+++ Starting migration {pg_table} -> {mssql_table}")

		# ============================================
		# PG CONNECT
		# ============================================
		pg_conn = psycopg2.connect(**CONFIG_PG)
		pg_cur	= pg_conn.cursor()
		pg_cur.execute(f"SELECT * FROM {pg_table}")
		headers = [d[0] for d in pg_cur.description]

		# ============================================
		# MSSQL CONNECT
		# ============================================

		conn_str = (
			f"DRIVER={CONFIG_MSSQL['driver']};"
			f"SERVER={CONFIG_MSSQL['server']};"
			f"DATABASE={CONFIG_MSSQL['database']};"
			f"UID={CONFIG_MSSQL['user']};"
			f"PWD={CONFIG_MSSQL['password']};"
			f"TrustServerCertificate=yes;"
		)

		ms_conn = pyodbc.connect(conn_str)
		ms_cur	= ms_conn.cursor()

		# Faster inserts
		ms_cur.fast_executemany = True

		# ============================================
		# EXISTING IDS
		# ============================================

		print("+++ Reading existing MSSQL IDs...")

		ms_cur.execute(
			f"SELECT {pk_field} FROM {mssql_table}"
		)

		existing_ids = set(r[0] for r in ms_cur.fetchall())

		print(f"+++ Existing IDs: {len(existing_ids)}")

		# ============================================
		# INSERT SQL
		# ============================================

		cols = ",".join(headers)

		placeholders = ",".join(["?"] * len(headers))

		sql = f"""
			INSERT INTO {mssql_table}
			({cols})
			VALUES ({placeholders})
		"""

		inserted = 0
		skipped = 0
		errors = 0

		# ============================================
		# PROCESS ROWS
		# ============================================

		while True:
			rows = pg_cur.fetchmany(batch_size)
			if not rows:
				break

			for row in rows:
				try:
					row_dict = dict(zip(headers, row))
					pk		 = row_dict[pk_field]

					# --------------------------------
					# Skip existing
					# --------------------------------
					if pk in existing_ids:
						skipped += 1
						continue

					# --------------------------------
					# Insert
					# --------------------------------
					ms_cur.execute(sql, row)
					inserted += 1
					existing_ids.add(pk)

					# Commit periodically
					if inserted % 500 == 0:
						ms_conn.commit()
						print(
							f"+++ inserted={inserted} "
							f"skipped={skipped} "
							f"errors={errors}"
						)

				except Exception as e:
					errors += 1
					print( f"ERROR inserting PK={pk}: {e}")
					# rollback only current failed tx
					ms_conn.rollback()
					continue

		# Final commit
		ms_conn.commit()

		# ============================================
		# CLOSE
		# ============================================
		pg_cur.close()
		pg_conn.close()

		ms_cur.close()
		ms_conn.close()

		print("\n+++ Migration completed")
		print(f"+++ inserted={inserted}")
		print(f"+++ skipped={skipped}")
		print(f"+++ errors={errors}")

	# ================================================
	# RUN IN BACKGROUND
	# ================================================
	#t = threading.Thread (target=worker, daemon=True)
	#t.start()
	worker ()
	print("+++ Migration launched in background")

#-----------------------------------------------------------------------
#-----------------------------------------------------------------------
def pg_to_csv(table, csv_file):
	conn = psycopg2.connect(**CONFIG_PG)
	cur = conn.cursor()

	cur.execute(f"SELECT * FROM {table}")

	headers = [d[0] for d in cur.description]

	with open(csv_file, "w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)

		writer.writerow(headers)

		for row in cur.fetchall():
			writer.writerow(row)

	cur.close()
	conn.close()

	print(f"OK: PostgreSQL -> CSV : {csv_file}")


def mysql_to_csv(table, csv_file):
	conn = mysql.connector.connect(**MYSQL_CONFIG)
	cur = conn.cursor()

	cur.execute(f"SELECT * FROM {table}")

	headers = [d[0] for d in cur.description]

	with open(csv_file, "w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)

		writer.writerow(headers)

		for row in cur.fetchall():
			writer.writerow(row)

	cur.close()
	conn.close()

	print(f"OK: MySQL -> CSV : {csv_file}")


def mssql_to_csv(table, csv_file):

	conn_str = (
		f"DRIVER={CONFIG_MSSQL['driver']};"
		f"SERVER={CONFIG_MSSQL['server']};"
		f"DATABASE={CONFIG_MSSQL['database']};"
		f"UID={CONFIG_MSSQL['user']};"
		f"PWD={CONFIG_MSSQL['password']};"
		f"TrustServerCertificate=yes;"
	)

	conn = pyodbc.connect(conn_str)

	cur = conn.cursor()

	cur.execute(f"SELECT * FROM {table}")

	headers = [d[0] for d in cur.description]

	with open(csv_file, "w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)

		writer.writerow(headers)

		for row in cur.fetchall():
			writer.writerow(row)

	cur.close()
	conn.close()

	print(f"OK: MSSQL -> CSV : {csv_file}")


# =========================================================
# IMPORT FUNCTIONS
# =========================================================

def csv_to_mysql(csv_file, table):

	conn = mysql.connector.connect(**MYSQL_CONFIG)

	cur = conn.cursor()

	with open(csv_file, newline="", encoding="utf-8") as f:

		reader = csv.reader(f)

		headers = next(reader)

		cols = ",".join(headers)

		placeholders = ",".join(["%s"] * len(headers))

		sql = f"""
			INSERT INTO {table}
			({cols})
			VALUES ({placeholders})
		"""

		for row in reader:
			cur.execute(sql, row)

	conn.commit()

	cur.close()
	conn.close()

	print(f"OK: CSV -> MySQL : {table}")


def csv_to_mssql(csv_file, table):

	conn_str = (
		f"DRIVER={CONFIG_MSSQL['driver']};"
		f"SERVER={CONFIG_MSSQL['server']};"
		f"DATABASE={CONFIG_MSSQL['database']};"
		f"UID={CONFIG_MSSQL['user']};"
		f"PWD={CONFIG_MSSQL['password']};"
		f"TrustServerCertificate=yes;"
	)

	conn = pyodbc.connect(conn_str)

	cur = conn.cursor()

	with open(csv_file, newline="", encoding="utf-8") as f:

		reader = csv.reader(f)

		headers = next(reader)
		# Remove id and created_by
		headers = headers [1:-1]

		cols = ",".join(headers)

		placeholders = ",".join(["?"] * len(headers))

		sql = f"""
			INSERT INTO {table}
			({cols})
			VALUES ({placeholders})
		"""

		for row in reader:
			row = getValidValues (row)
			cur.execute(sql, row)

	conn.commit()

	cur.close()
	conn.close()

	print(f"OK: CSV -> MSSQL : {table}")


def csv_to_pg(csv_file, table):

	conn = psycopg2.connect(**CONFIG_PG)

	cur = conn.cursor()

	with open(csv_file, newline="", encoding="utf-8") as f:

		reader = csv.reader(f)

		headers = next(reader)

		# Remove id and created_by
		headers = headers [1:-1]
		print (f"\n+++ {headers=}")

		print (f"+++ {len (headers)=}")
		input ("Continue...")

		cols = ",".join(headers)
		placeholders = ",".join(["%s"] * len(headers))

		sql = f"""
			INSERT INTO {table}
			({cols})
			VALUES ({placeholders})
		"""
		print (f"\n+++ {sql=}")

		for row in reader:
			row = getValidValues (row)
#			row	= row [1:-1]
#			# Check valid dates or set to None
#			row [0]  = row [0] if row [0] else None
#			row [-3] = row [-3] if row [-3] else None

			cur.execute(sql, row)
			#option = input ("Continue...")
			#if option != "yes":
			#	break

	conn.commit()

	cur.close()
	conn.close()

	print(f"OK: CSV -> PostgreSQL : {table}")

# =========================================================
# MAIN
# =========================================================

def main():

	if len(sys.argv) < 4:

		print(__doc__)
		sys.exit(1)

	cmd = sys.argv[1]

	if cmd == "pg_to_csv":

		table = sys.argv[2]
		csv_file = sys.argv[3]

		pg_to_csv(table, csv_file)

	elif cmd == "mysql_to_csv":

		table = sys.argv[2]
		csv_file = sys.argv[3]

		mysql_to_csv(table, csv_file)

	elif cmd == "mssql_to_csv":

		table = sys.argv[2]
		csv_file = sys.argv[3]

		mssql_to_csv(table, csv_file)

	elif cmd == "csv_to_mysql":

		csv_file = sys.argv[2]
		table = sys.argv[3]

		csv_to_mysql(csv_file, table)

	elif cmd == "csv_to_mssql":
		csv_file = sys.argv[2]
		table = sys.argv[3]
		csv_to_mssql(csv_file, table)

	elif cmd == "csv_to_pg":
		csv_file = sys.argv[2]
		table = sys.argv[3]
		csv_to_pg(csv_file, table)

	elif cmd == "pg_to_mssql":
		tablePG = sys.argv[2]
		tableMS = sys.argv[3]
		pg_to_mssql (tablePG, tableMS)

	else:
		print("Invalid command")


if __name__ == "__main__":
	main()
