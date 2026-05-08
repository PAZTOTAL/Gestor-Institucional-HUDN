#!/usr/bin/env python3

import os
import subprocess
import psycopg2


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def full_setup ():
	set_env_vars ()
	env = get_env_vars ()
	answer = input ("SEGURO DE ELIMINAR LA BD '%s'? " % env ['dbname'])  
	if answer != 'YES':
		return
	os.system ("dropdb %s" % env ['dbname'])
	#create_pg_user (env["user"], env["password"])
	create_database (env["dbname"], env["user"])
	init_django (env['settings'])
	reset_migrations_safe ()

	create_initial_app_admin_user (env)

# ─────────────────────────────────────────────────────────────
# 0. Set ENV
# ─────────────────────────────────────────────────────────────
def set_env_vars ():
	os.environ['PGDATABASE']   = 'crue_traslados_db'
	os.environ['PGHOST']	   = '127.0.0.1'
	os.environ['PGPORT']	   = '5432'
	os.environ['PGUSER']	   = 'postgres'
	os.environ['PGPASSWORD']   = 'postgres2026'
	DATABASE = f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}"
	os.environ['DATABASE_PUBLIC_URL'] = DATABASE
	os.environ['DATABASE_URL'] = DATABASE
	os.environ['PGSETTINGS']   = 'config.settings'

# ─────────────────────────────────────────────────────────────
# 1. Load ENV
# ─────────────────────────────────────────────────────────────
def get_env_vars ():
	return {
		"dbname": os.getenv ("PGDATABASE"),
		"user": os.getenv ("PGUSER"),
		"password": os.getenv ("PGPASSWORD"),
		"host": os.getenv ("PGHOST", "127.0.0.1"),
		"port": os.getenv ("PGPORT", "5432"),
		"settings": os.getenv  ("PGSETTINGS"),
		"adminUser": 'postgres',
		"adminPaswd": 'postgres2026'
	}

# ─────────────────────────────────────────────────────────────
# 0. Create initial application user
# ─────────────────────────────────────────────────────────────
def create_initial_app_admin_user (env):
	from django.contrib.auth import get_user_model
	from django.db import transaction

	init_django (env['settings'])
	User = get_user_model()

	username = "admin"
	password = "admin2026"

	with transaction.atomic():
		user, created = User.objects.get_or_create(
			username=username,
			defaults={
				"email": "admin@gmail.com",
				"first_name": "Administrador CRUE",
				"rol": "DIRECTOR",
				"is_staff": True,
				"is_superuser": True,
				"is_active": True,
			}
		)

		if created:
			user.set_password(password)
			user.save()
			print("✅ Admin user created")
		else:
			# ensure password and critical fields are correct
			user.set_password(password)
			user.email = "admin@gmail.com"
			user.nombre = "Administrador CRUE"
			user.rol = "DIRECTOR"
			user.is_staff = True
			user.is_superuser = True
			user.is_active = True
			user.save()

			print("ℹ️ Admin user already existed → updated")

# ─────────────────────────────────────────────────────────────
# 2. Init Django environment
# ─────────────────────────────────────────────────────────────
def init_django (settings):
	import django
	print (f"+++ Init django...")
	os.environ.setdefault ("DJANGO_SETTINGS_MODULE", settings)
	django.setup ()
	print ("✅ Django initialized")


# ─────────────────────────────────────────────────────────────
# 3. Connect to postgres  (admin DB)
# ─────────────────────────────────────────────────────────────
def get_admin_connection ():
	env = get_env_vars ()
	return psycopg2.connect (
		dbname="postgres",	# connect to default DB
		user=env["adminUser"],
		password=env["adminPaswd"],
		host=env["host"],
		port=env["port"],
	)


# ─────────────────────────────────────────────────────────────
# 4. Create PostgreSQL user
# ─────────────────────────────────────────────────────────────
def create_pg_user (new_user, new_password):
	print (f"+++ Creating PG user {new_user=}")
	conn = get_admin_connection ()
	conn.autocommit = True
	cur = conn.cursor ()

	try:
		cur.execute (f"""
			DO $$
			BEGIN
				IF NOT EXISTS  (
					SELECT FROM pg_catalog.pg_roles WHERE rolname = %s
				) THEN
					CREATE ROLE {new_user} LOGIN PASSWORD %s;
				END IF;
			END
			$$;
		""",  (new_user, new_password))
		print (f"✅ User '{new_user}' ensured")
	finally:
		cur.close ()
		conn.close ()


# ─────────────────────────────────────────────────────────────
# 5. Create database
# ─────────────────────────────────────────────────────────────
from psycopg2 import sql

def create_database (dbname, owner):
	conn = get_admin_connection()
	conn.autocommit = True
	cur = conn.cursor()

	try:
		# 1. Check if DB exists
		cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (dbname,))
		exists = cur.fetchone()

		if not exists:
			cur.execute(
				sql.SQL("CREATE DATABASE {} OWNER {};")
				.format(
					sql.Identifier(dbname),
					sql.Identifier(owner)
				)
			)
			print(f"✅ Database '{dbname}' created")
		else:
			print(f"ℹ️ Database '{dbname}' already exists")

	except Exception as ex:
		print (f"+++ {ex=}")

	finally:
		cur.close()
		conn.close()

	# 2. Grant permissions inside the DB
	#grant_db_permissions(dbname, owner)

def grant_db_permissions(dbname, user):
	env = get_env_vars()

	conn = psycopg2.connect(
		dbname=dbname,
		user=env["user"],  # admin user
		password=env["password"],
		host=env["host"],
		port=env["port"],
	)
	conn.autocommit = True
	cur = conn.cursor()

	try:
		# Schema usage
		cur.execute(sql.SQL("GRANT ALL ON SCHEMA public TO {};")
					.format(sql.Identifier(user)))

		# Tables
		cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {};")
					.format(sql.Identifier(user)))

		# Sequences (important for Django AutoField)
		cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {};")
					.format(sql.Identifier(user)))

		# Future tables/sequences (VERY important)
		cur.execute(sql.SQL("""
			ALTER DEFAULT PRIVILEGES IN SCHEMA public
			GRANT ALL ON TABLES TO {};
		""").format(sql.Identifier(user)))

		cur.execute(sql.SQL("""
			ALTER DEFAULT PRIVILEGES IN SCHEMA public
			GRANT ALL ON SEQUENCES TO {};
		""").format(sql.Identifier(user)))

		print(f"✅ Permissions granted to '{user}' on DB '{dbname}'")
	except Exception as ex:
		print (f"+++ {ex=}")

	finally:
		cur.close()
		conn.close()

# ─────────────────────────────────────────────────────────────
# 6. Reset migrations  (Django)
# ─────────────────────────────────────────────────────────────
import os
import subprocess
from django.conf import settings
from django.apps import apps

def reset_migrations_safe():
	print("+++ Resetting migrations (SAFE)...")

	project_apps = set(settings.INSTALLED_APPS)

	for app in apps.get_app_configs():

		# Skip Django internal apps
		if app.name not in project_apps:
			continue

		# Skip contrib apps explicitly (extra safety)
		if app.name.startswith("django."):
			continue

		migrations_path = os.path.join(app.path, "migrations")

		if not os.path.exists(migrations_path):
			continue

		for f in os.listdir(migrations_path):
			full_path = os.path.join(migrations_path, f)

			# skip init + directories
			if f == "__init__.py" or os.path.isdir(full_path):
				continue

			os.remove(full_path)
			print(f"Deleted: {app.label}/{f}")

	subprocess.run(["python", "manage.py", "makemigrations"], check=True)
	subprocess.run(["python", "manage.py", "migrate"], check=True)

	print("✅ Migrations reset safely")
# ─────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
	full_setup ()
