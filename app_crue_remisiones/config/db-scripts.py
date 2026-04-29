#!/usr/bin/env python3

"""
Scrips for handling re-create EcuapassDocs as
recreate DB, USER, data, and MIGRATIONS
"""
import os, sys
import subprocess as sb
import psycopg2

import django
from django.contrib.auth.hashers import make_password
from urllib.parse import urlparse
import traceback # format_exc

#----------------------------------------------------------
#-- Parse a database URL (e.g. Railway PostgreSQL URL) into components.
#----------------------------------------------------------
def getVarsFromDBUrl(db_url: str) -> dict:
	p = urlparse(db_url)
	return { "USER":p.username, "PASSWORD":p.password, "HOST":p.hostname, "DATABASE":p.path[1:], "PORT":p.port or 5432 }

#----------- POSTGRES DB SETUP ---------------------------------------------------------------
PROJECT_ROOT = os.path.join (os.getcwd())
APPPATH      = PROJECT_ROOT

#-- Postgres vars
DATABASE_PUBLIC_URL = os.environ.get ("DATABASE_PUBLIC_URL") ; print ("\t", DATABASE_PUBLIC_URL)
PG    = getVarsFromDBUrl (DATABASE_PUBLIC_URL)
print (f"+++ {PG=}")

print ("Postgres DB settings:")
PGUSER, PGPASSWORD = PG ['USER'], PG ['PASSWORD']
PGDATABASE, PGHOST, PGPORT = PG ['DATABASE'], PG ['HOST'],PG ['PORT'],
DB_PARAMS  = {'dbname':PGDATABASE, 'user':PGUSER, 'password':PGPASSWORD, 'host':PGHOST,'port': PGPORT}

# initSettings ()
sys.path.insert (0, PROJECT_ROOT)  # Add project root to Python path
os.environ["DATABASE_URL"] = DATABASE_PUBLIC_URL
os.environ.setdefault ("DJANGO_SETTINGS_MODULE", "app_main.settings") #appdocs_main") #/settings")
django.setup ()

#---------------------------------------------------------------------------------------------
# Main
#---------------------------------------------------------------------------------------------
def main ():
	pass
#	dropUserAndDatabase ()
#	createDBUserAndDatabase ()
#	resetMigrations ()
#	runMigrations ()
	createAdminEmpresa ()
	createAdminUser ()
#	addExtensions ()
#	runCollectStatics ()
#	deleteDBTestData ()
#	populateDBWithTestData ()

	#---
	#createPublicSchemaGrantUser ()
	#checkUserPrivileges ()
	#viewSchemasAndOwnership ()
	#checkForOwnedObjects ()
	#dropOwnedObjects ()

#----------------------------------------------------------
# Set up Django environment
#----------------------------------------------------------
def initSettings ():
	sys.path.insert (0, PROJECT_ROOT)  # Add project root to Python path
	os.environ.setdefault ("DJANGO_SETTINGS_MODULE", "app_main.settings") #appdocs_main") #/settings")
	django.setup ()

#----------------------------------------------------------
#-- Drop current DB user and database
#----------------------------------------------------------
def dropUserAndDatabase ():
	if input (f"Remove USER: {PGUSER} and DATABASE: {PGDATABASE} : (yes/no) ") == "yes":
		exe (f"drop database IF EXISTS {PGDATABASE};", DB='postgres')
		exe (f"drop user IF EXISTS $PGUSER;", SUPER=True)

#----------------------------------------------------------
#-- Create DB user, DB, and grant permissions
# Create PostgreSQL role and database
#----------------------------------------------------------
def createDBUserAndDatabase ():
	sql = f"createuser -d {PGUSER}"; exe (sql, SQL=False)
	sql = f"ALTER USER {PGUSER} WITH PASSWORD '{PGPASSWORD}';"; exe (sql, SUPER=True)
	sql = f"CREATE DATABASE {PGDATABASE} OWNER {PGUSER};" ; exe (sql, SUPER=True)
	sql = f"GRANT ALL PRIVILEGES ON DATABASE {PGDATABASE} TO {PGUSER};"; exe (sql)
	sql = f"ALTER SCHEMA public OWNER TO {PGUSER};"; exe (sql, DB=PGDATABASE)

#----------------------------------------------------------
# Remove old migrations and make new migrations
#----------------------------------------------------------
def resetMigrations ():
	appsList = [x for x in os.listdir (".") if x.startswith ("app_")]

	#	appsList = ["app_usuarios", "app_docs", "app_cartaporte", "app_manifiesto", "app_declaracion"]

	for app in appsList:
		cmm = f"rm {APPPATH}/{app}/migrations/00*.py"
		print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

#----------------------------------------------------------
#-- Run migrations and create superuser
#----------------------------------------------------------
def runMigrations ():
	cmm = f"python3 {APPPATH}/manage.py flush --noinput"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	cmm = f"python3 {APPPATH}/manage.py makemigrations"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

	cmm = f"python3 {APPPATH}/manage.py migrate"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)

#----------------------------------------------------------
# Create admin user and set pais="TODOS"
#----------------------------------------------------------
def createAdminEmpresa ():
	from app_usuarios.models import Empresas
	Empresas.objects.create (nickname="fronteria", nombre="FRONTERIA SOFTWARE", permiso="PO-CO-0000-00", 
		id_tipo="NIT", id_numero="000.000.000.0",
		direccion="CALLE 17 # 1A-17",
		telefono="3176753141 Ipiales-Colombia"
	)

def createAdminUser ():
	from app_usuarios.models import Empresas, Usuarios
	empresa = Empresas.objects.get (nickname="fronteria")

	Usuarios.objects.create_user(usernick="lgx",
		username="fronteria_lgx", email="lgx@gmail.com", password="lge",   # Default fields
		empresa=empresa, pais="TODOS", perfil="SUPER",           # Model fields
		is_staff=True, is_superuser=True                         # Superuser fields
	)

#-- Create extension for advanced text searches
def addExtensions ():
	sql = f"CREATE EXTENSION IF NOT EXISTS pg_trgm;"; 
	exe (sql, DB=PGDATABASE)

#----------------------------------------------------------
# Collect migrations
#----------------------------------------------------------
def runCollectStatics ():
	cmm = f"python3 {APPPATH}/manage.py collectstatic --noinput"
	print (cmm) ; sb.run (cmm, shell=True, env=os.environ)


#----------------------------------------------------------
# Populate DB with Test Data (clientes, conductores, vehiculos)
#----------------------------------------------------------
def deleteDBTestData ():
	tableList = [
			"usuario", 
			"empresa",
			"cliente", "conductor", "vehiculo"]
	try:
		for table in tableList:
			query = psycopg2.sql.SQL (f'TRUNCATE TABLE {table} CASCADE;')
			execute_sql_query (query)
	except:
		print (">>> Exception en:", table, data)
		print (traceback.format_exc())


def populateDBWithTestData ():
	clientes_data = [
		(1001, '1020', "NIT", "CHEVROLET S.A", "AV. COLON", "CALI", "COLOMBIA", 11),
		(1002, '1030', "RUC", "MAZDA S.A.", "AV. RIO", "IBARRA",  "ECUADOR", 11),
		(1003, '1040', "RUC", "RENAULT S.A.", "AV. CIRC", "QUITO", "ECUADOR", 11) ]

	conductores_data = [
		(1001, '11030', "LUIS GARRETA", "ECUADOR", "1103011", "CC", "1990-12-31",None,None,11),
		(1002, '11020', "JAIRO MORA", "COLOMBIA", "1102011", "CC", "1990-10-25",None,1001,11 ),
		(1003, '99040', "JAIRO GARRETA", "PERU", "9904011", "CC", "1995-05-22",None,None,11),
		(1004, '11040', "LUIS DIAZ", "COLOMBIA", "1104011", "CC", "2000-05-22",None,None,11) ]

	vehiculos_data = [
		(1001, 'PNA12A', "CHEVROLET", "COLOMBIA", "1020", "2000",None,None,1004,11,None ),
		(1002, 'PNB12B', "MAZDA", "ECUADOR", "1030", "1999",None,None,1001,11,None ),
		(1003, 'PNC12C', "RENAULT", "ECUADOR", "1040", "1995",None,None,1003,11,None ) ]

	#------------------------------------------------------------------------
	def populate_database (data, table, empresa_id):
		print (f"\n+++ Populating DB::'{table=}'")
		try:
			for entry in data:
				placeholders = ', '.join(['%s'] * len(entry))
				query = psycopg2.sql.SQL("INSERT INTO {} VALUES ({})").format(
					psycopg2.sql.Identifier(table),
					psycopg2.sql.SQL(placeholders)
				)				 
				execute_sql_query (query, entry)
		except:
			print (">>> Exception en:", table, data)
			print (traceback.format_exc())

	def populate_empresas ():
		print (f"\n+++ Populating DB::empresa")
		from app_usuarios.models import Empresas
		Empresas.objects.create (id=22, nickname="byza", nombre="GRUPO BYZA", permiso="PO-CO-0033-22", 
			id_tipo="NIT", id_numero="900.168.467-2",
			direccion="CRA 1 No 1-15 AV PANAMERICANA",
			telefono="TEL (092)7250934 FAX:(092)7251311\nIpiales-Colombia",
			otra_info=""
		)
		Empresas.objects.create (id=33, nickname="logitrans", nombre="TRANSPORTES LOGITRANS-ACROS S.A.", permiso="PO-EC-0005-20", 
			id_tipo="RUC", id_numero="0491507748001",
			direccion="CALDERON NRO. 63-052 Y URUGUAY",
			telefono="Tel: 062962548\nTulcan - Ecuador",
			otra_info="Sucursal COLOMBIA Cra 7 No 12A 108 Ed. Cordoba\nAviles P. 5 Of 502 Tel: 7733227 Ipiales; PERU Cll 7 de\nEnero No. 506 B/ Bellavista Tel: 972942173 Tumbes"
		)

	def populate_usuarios ():
		print (f"\n+++ Populating DB::usuario")
		from app_usuarios.models import Usuarios
		Usuarios.objects.create (username="lgb", empresa_id=11, password=make_password ('lge'), email="lgb@gmail.com",
						  pais="COLOMBIA", perfil="funcionario")
		Usuarios.objects.create (username="lgl", empresa_id=12, password=make_password ('lge'), email="lgl@gmail.com",
						  pais="ECUADOR", perfil="funcionario")
		Usuarios.objects.create (username="lgx", empresa_id=11, password=make_password ('lge'), email="lgx@gmail.com",
						  pais="TODOS", perfil="director", is_superuser=True, is_staff=True)
	
	#------------------------------------------------------------------------
	populate_empresas ()
#	populate_usuarios ()
#
#	empresa_id = 11
#	populate_database (clientes_data, "cliente", empresa_id)
#	populate_database (conductores_data, "conductor", empresa_id)
#	populate_database (vehiculos_data, "vehiculo", empresa_id)

#----------------------------------------------------------
# Execute query from linux shell
#----------------------------------------------------------
def exe (sql, SQL=True, SUPER=False, PROMPT=False, DB=""):
	cmm = ""
	if not SQL:
		cmm = f"sudo -u postgres {sql}"; 
	elif not SUPER:
		cmm = f"psql {DB} -c \"{sql}\""; 
	else:
		cmm = f"sudo -u postgres psql {DB} -c \"{sql}\""; 

	print ("-----------------------------------------------")
	print (cmm)
	print ("-----------------------------------------------")
	if not PROMPT:
		sb.run (cmm, shell=True, env=os.environ)
	else:
		if input ("\nARE YOU SURE ? (YES/NO): ") == "YES":
			sb.run (cmm, shell=True, env=os.environ)
		else:
			print ("NO ACTION")

#--------------------------------------------------------------------
# Execute query from DJango API
#--------------------------------------------------------------------
def execute_sql_query (query, values=None):
	print (f"+++ DEBUG: query '{query}'")
	print (f"+++ DEBUG: values '{values}'")
	conn = psycopg2.connect(**DB_PARAMS)
	with conn.cursor() as cursor:
		cursor.execute(query, values)
	conn.commit()
	conn.close()

#----------------------------------------------------------
#-- Check current user's privileges on the public schema
#----------------------------------------------------------
def checkUserPrivileges ():
	exe (f"SELECT * FROM information_schema.schema_privileges" \
	     f" WHERE grantee = '{PGUSER}' AND schema_name = 'public';")
#----------------------------------------------------------
#-- View Schemas and Their Ownership with Permissions:
#----------------------------------------------------------
def viewSchemasAndOwnership ():
	sql = "SELECT n.nspname AS schema_name, r.rolname AS owner, \
has_schema_privilege(r.rolname, n.nspname, 'USAGE') AS usage, \
has_schema_privilege(r.rolname, n.nspname, 'CREATE') AS create \
FROM pg_catalog.pg_namespace n \
JOIN pg_catalog.pg_roles r ON n.nspowner = r.oid \
ORDER BY schema_name;"
	exe (sql, DB=PGDATABASE)

#----------------------------------------------------------
#-- Check for Owned Objects:
#----------------------------------------------------------
def checkForOwnedObjects ():
	sql = "SELECT n.nspname AS schema_name, r.rolname AS owner \
FROM pg_catalog.pg_namespace n \
JOIN pg_catalog.pg_roles r ON n.nspowner = r.oid \
WHERE r.rolname = 'your_user';"
	exe (sql)

#----------------------------------------------------------
##-- Drop Owned Objects:
#----------------------------------------------------------
def dropOwnedObjects ():
	sql = f"DROP OWNED BY {PGUSER};"
	exe (sql, PROMPT=True)

#----------------------------------------------------------
#-- Show current schemas
#----------------------------------------------------------
def showCurrentSchemas ():
	sql = "SELECT schema_name FROM information_schema.schemata;"
	exe (sql)

#----------------------------------------------------------
# For changing DB user password as user 'postgres'
#----------------------------------------------------------
def changePasswordDBUser (dbUser, newPassword):
	sql = f"ALTER USER {dbUser} WITH PASSWORD '{newPassword}';"
	exe (sql)

#----------------------------------------------------------
#-- Create public schema and grants to user
#----------------------------------------------------------
def createPublicSchemaGrantUser ():
	sql = "CREATE SCHEMA public;"; exe (sql)
	sql = f"ALTER SCHEMA public OWNER TO {PGUSER};"; exe (sql)
	sql = f"GRANT USAGE ON SCHEMA public TO PUBLIC;"; exe (sql)
	sql = f"GRANT CREATE ON SCHEMA public TO {PGUSER}"; exe (sql)


#----------------------------------------------------------
#-- Call to main
#----------------------------------------------------------
main ()
