import os, psycopg2
from urllib.parse import urlparse
import traceback    # format_exc

class Utils:


	#------------------------------------------------------------------------------
	#------------------------------------------------------------------------------
	def cargarPacientesProgramadosCirugia ():
		"""Limpia pacientes y sesiones existentes, y carga los pacientes programados para cirugía."""
		from app_core.models import Paciente, Sesion

		pacientes_data = [
			{'id': 11, 'identificacion': 'Jorge Ra.',  'nombre': 'Jorge Rámirez',    'origen': 'PROGRAMADO'},
			{'id': 12, 'identificacion': 'Maria Be.',  'nombre': 'María Belen',      'origen': 'PROGRAMADO'},
			{'id': 13, 'identificacion': 'Lina M.',    'nombre': 'Lina Montoya',     'origen': 'PROGRAMADO'},
			{'id': 14, 'identificacion': 'Alberto C.', 'nombre': 'Alberto Camargo',  'origen': 'PROGRAMADO'},
			{'id': 15, 'identificacion': 'Diana U.',   'nombre': 'Diana Uribe',      'origen': 'PROGRAMADO'},
			{'id': 16, 'identificacion': 'Adrian C.',  'nombre': 'Adrian Cifuentes', 'origen': 'PROGRAMADO'},
		]

		# CASCADE via ORM: deleting Paciente also deletes its Sesiones
		Paciente.objects.all ().delete ()

		print (f"\n+++ Creando pacientes PROGRAMADOS...")
		for datos in pacientes_data:
			Paciente.objects.create (**datos)

		print (f"+++ {len (pacientes_data)} pacientes cargados.")

	#----------------------------------------------------------
	#-- Print exception with added 'message' and 'text'
	#----------------------------------------------------------
	def printException (message, docFilepath=None):
		try:
			stackTrace = ''.join(traceback.format_exc())
			orgMessage = f"{message}:\n{stackTrace}"
			open ("log-exceptions.log", "a").write (orgMessage)
			print (orgMessage)
		except Exception as ex:
			print (f"+++ Error en printException. Message: {message}")
			pass
	#----------------------------------------------------------
	#-- Parse a database URL (e.g. Railway PostgreSQL URL) into components.
	#----------------------------------------------------------
	def getVarsFromDBUrl(db_url: str) -> dict:
		p = urlparse(db_url)
		return { "user":p.username, "password":p.password, "host":p.hostname, "dbname":p.path[1:], "port":p.port or 5432 }

	#--------------------------------------------------------------------
	# Execute query from DJango API
	#--------------------------------------------------------------------
	def execute_sql_query (query, values=None):
		print (f"+++ DEBUG: query '{query}'")
		print (f"+++ DEBUG: values '{values}'")
		DB_PARAMS = Utils.getVarsFromDBUrl (os.environ.get ("DATABASE_URL"))
		conn = psycopg2.connect(**DB_PARAMS)
		with conn.cursor() as cursor:
			cursor.execute(query, values)
		conn.commit()
		conn.close()
	
