"""
Management command: cargar_datos_legacy
Carga los datos del sistema antiguo (MySQL/defenjur) al nuevo sistema Django (SQL Server).
Uso: python manage.py cargar_datos_legacy
     python manage.py cargar_datos_legacy --limpiar   (borra antes de insertar)
"""
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from datetime import datetime
from legal.models import (
    ProcesoExtrajudicial, ProcesoJudicialActiva, ProcesoJudicialPasiva,
    AccionTutela, DerechoPeticion, Peritaje, PagoSentenciaJudicial,
    ProcesoJudicialTerminado, ProcesoAdministrativoSancionatorio,
    RequerimientoEnteControl, Usuario
)


def _dt(s):
    """Convierte string datetime de MySQL a datetime aware de Django."""
    if not s:
        return None
    try:
        return make_aware(datetime.strptime(s, '%Y-%m-%d %H:%M:%S'))
    except Exception:
        return None


class Command(BaseCommand):
    help = 'Carga los datos del sistema antiguo (defenjur MySQL) al nuevo sistema Django.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina los registros existentes antes de cargar (usar con precaucion).'
        )

    def handle(self, *args, **options):
        if options['limpiar']:
            self.stdout.write(self.style.WARNING('[!] Limpiando tablas existentes...'))
            ProcesoExtrajudicial.objects.all().delete()
            ProcesoJudicialActiva.objects.all().delete()
            ProcesoJudicialPasiva.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('[OK] Tablas limpiadas.'))

        self._cargar_extrajudiciales()
        self._cargar_procesos_activos()
        self._cargar_procesos_pasivos()
        self._cargar_usuarios()

        self.stdout.write(self.style.SUCCESS('\n[LISTO] Migracion completada exitosamente.'))

    # ------------------------------------------------------------------
    # Procesos Extrajudiciales
    # ------------------------------------------------------------------
    def _cargar_extrajudiciales(self):
        self.stdout.write('\n[>] Cargando Procesos Extrajudiciales...')

        datos = [
            {
                'demandante': 'Magali',
                'demandado': 'HUDN',
                'apoderado': 'Sara Rivera',
                'medio_control': 'Ejecutivo',
                'despacho_conocimiento': 'sdfswqerwer',
                'estado': 'Conciliado',
                'clasificacion': '',
                'fecha_registro': _dt('2024-12-01 17:41:53'),
            },
            {
                'demandante': 'Felipe Vega',
                'demandado': 'Hosdenar',
                'apoderado': 'Sara Rivera',
                'medio_control': 'Accion de Repeticion',
                'despacho_conocimiento': 'sdfsdfsdf',
                'estado': 'Conciliado',
                'clasificacion': '',
                'fecha_registro': _dt('2024-12-01 19:05:39'),
            },
            {
                'demandante': 'sdefsdf',
                'demandado': 'sdfs',
                'apoderado': 'dfsdfsdf',
                'medio_control': 'Nulidad y Reestablecimiento del Derecho',
                'despacho_conocimiento': 'sdfsdf',
                'estado': 'No conciliado',
                'clasificacion': '',
                'fecha_registro': _dt('2024-12-01 19:06:48'),
            },
        ]

        creados = 0
        for d in datos:
            obj, created = ProcesoExtrajudicial.objects.get_or_create(
                demandante=d['demandante'],
                demandado=d['demandado'],
                apoderado=d['apoderado'],
                defaults=d
            )
            if created:
                creados += 1
                self.stdout.write(f'   [+] Creado: {obj.demandante} vs {obj.demandado}')
            else:
                self.stdout.write(f'   [=] Ya existe: {obj.demandante} vs {obj.demandado}')

        self.stdout.write(self.style.SUCCESS(
            f'   --> {creados} nuevos registros extrajudiciales cargados.'
        ))

    # ------------------------------------------------------------------
    # Procesos Judiciales Activos
    # ------------------------------------------------------------------
    def _cargar_procesos_activos(self):
        self.stdout.write('\n[>] Cargando Procesos Judiciales Activos (Posicion Activa)...')

        datos = [
            {
                'num_proceso': '2016-00109',
                'medio_control': 'Ejecutivo',
                'demandante': 'HUDN',
                'demandado': 'EKITEC',
                'apoderado': 'Sara Rivera',
                'despacho_actual': 'Octavo Administrativo',
                'ciudad': 'San Juan de Pasto',
                'pretension': (
                    'Declarar la liquidacion judicial del contrato '
                    'No. 120.SAF-0496.2014'
                ),
                'estimacion_cuantia': '251625499',
                'sentencia_primera_instancia': '31/10/2019',
                'ultima_actuacion': (
                    'el 23 de junio de 2019 se radico alegatos de conclusion '
                    'en primera instancia. 31 de octubre de 2019 sentencia que '
                    'nego pretensiones de la demanda. Apelacion presentada el 22 '
                    'de noviembre de 2019 (correo electronico) y el 25 de noviembre '
                    'de 2019 en fisico. Pendiente tramite apelacion'
                ),
                'estado_actual': (
                    'El 26 de julio de 2023 se llevo a cabo audiencia inicial y se '
                    'dijo fecha para audiencia de pruebas para febrero de 2024, el '
                    '19 de febrero de 2024 Se asistio a audiencia de pruebas-el 29 '
                    'de febrero de 2024 se asistio a continuacion de audiencia de '
                    'pruebas, El 13 de marzo de 2024 Se presento escrito de alegatos '
                    'de conclusion de primera instancia-PENDIENTE SENTENCIA DE PRIMERA INSTANCIA'
                ),
                'fecha_registro': _dt('2024-12-01 21:48:46'),
            },
            {
                'num_proceso': '2016-00109',
                'medio_control': 'Controversias contractuales',
                'demandante': 'HUDN',
                'demandado': 'EKITEC',
                'apoderado': 'Sara Rivera',
                'despacho_actual': 'Octavo Administrativo',
                'ciudad': 'San Juan de Pasto',
                'pretension': (
                    'Declarar la liquidacion judicial del contrato '
                    'No. 120.SAF-0496.2014'
                ),
                'estimacion_cuantia': '251625499',
                'sentencia_primera_instancia': '31/10/2019',
                'ultima_actuacion': (
                    'el 23 de junio de 2019 se radico alegatos de conclusion '
                    'en primera instancia. 31 de octubre de 2019 sentencia que '
                    'nego pretensiones de la demanda. Apelacion presentada el 22 '
                    'de noviembre de 2019 (correo electronico) y el 25 de noviembre '
                    'de 2019 en fisico. Pendiente tramite apelacion'
                ),
                'estado_actual': (
                    'El 26 de julio de 2023 se llevo a cabo audiencia inicial y se '
                    'dijo fecha para audiencia de pruebas para febrero de 2024, el '
                    '19 de febrero de 2024 Se asistio a audiencia de pruebas-el 29 '
                    'de febrero de 2024 se asistio a continuacion de audiencia de '
                    'pruebas, El 13 de marzo de 2024 Se presento escrito de alegatos '
                    'de conclusion de primera instancia-PENDIENTE SENTENCIA DE PRIMERA INSTANCIA'
                ),
                'fecha_registro': _dt('2024-12-01 21:57:10'),
            },
        ]

        creados = 0
        for d in datos:
            obj, created = ProcesoJudicialActiva.objects.get_or_create(
                num_proceso=d['num_proceso'],
                medio_control=d['medio_control'],
                demandado=d['demandado'],
                defaults=d
            )
            if created:
                creados += 1
                self.stdout.write(
                    f'   [+] Creado: #{d["num_proceso"]} - {d["medio_control"]}'
                )
            else:
                self.stdout.write(
                    f'   [=] Ya existe: #{d["num_proceso"]} - {d["medio_control"]}'
                )

        self.stdout.write(self.style.SUCCESS(
            f'   --> {creados} nuevos registros activos cargados.'
        ))

    # ------------------------------------------------------------------
    # Procesos Judiciales Pasivos
    # ------------------------------------------------------------------
    def _cargar_procesos_pasivos(self):
        self.stdout.write('\n[>] Cargando Procesos Judiciales Pasivos...')

        datos = [
            {
                'num_proceso': 'wwwwwwwwwwwwwww',
                'medio_control': 'Nulidad',
                'demandante': '324234',
                'cc_demandante': '234',
                'demandado': 'wsesdf',
                'apoderado': 'felipe',
                'despacho_actual': 'sdf',
                'pretensiones': None,
                'valor_pretension_inicial': 'dfdfs',
                'valor_provisionar': 'dfe',
                'fallo_sentencia': '34',
                'valor_fallo_sentencia': None,
                'estado_actual': 'sdfsdf',
                'riesgo_perdida': '23423',
                'porcentaje_probabilidad_perdida': None,
                'hechos_relevantes': 'sdf',
                'enfoque_defensa': '234',
                'calidad_entidad': '',
                'hecho_generador': 'sdf',
                'observaciones': 'texot',
                'fecha_registro': _dt('2024-12-01 20:15:33'),
            },
            {
                'num_proceso': '111111111111111111111',
                'medio_control': 'Ejecutivo',
                'demandante': '324234',
                'cc_demandante': '234',
                'demandado': 'wsesdf',
                'apoderado': '2322222222222222222222',
                'despacho_actual': 'sdf',
                'pretensiones': None,
                'valor_pretension_inicial': 'dfdfs',
                'valor_provisionar': 'dfe',
                'fallo_sentencia': '34',
                'valor_fallo_sentencia': None,
                'estado_actual': 'sdfsdf',
                'riesgo_perdida': '23423',
                'porcentaje_probabilidad_perdida': None,
                'hechos_relevantes': 'sdf',
                'enfoque_defensa': '234',
                'calidad_entidad': 'Victima',
                'hecho_generador': 'sdf',
                'observaciones': 'ssdf',
                'fecha_registro': _dt('2024-12-01 20:22:35'),
            },
            {
                'num_proceso': 'zzzzzzzzzzzzzzzzzzz',
                'medio_control': 'Accion de Repeticion',
                'demandante': '324234',
                'cc_demandante': '234',
                'demandado': 'wsesdf',
                'apoderado': 'felipe',
                'despacho_actual': 'sdf',
                'pretensiones': None,
                'valor_pretension_inicial': 'dfdfs',
                'valor_provisionar': 'dfe',
                'fallo_sentencia': '34',
                'valor_fallo_sentencia': None,
                'estado_actual': 'sdfsdf',
                'riesgo_perdida': '23423',
                'porcentaje_probabilidad_perdida': None,
                'hechos_relevantes': 'sdf',
                'enfoque_defensa': '234',
                'calidad_entidad': '',
                'hecho_generador': 'sdf',
                'observaciones': 'texot',
                'fecha_registro': _dt('2024-12-01 21:27:55'),
            },
        ]

        creados = 0
        for d in datos:
            obj, created = ProcesoJudicialPasiva.objects.get_or_create(
                num_proceso=d['num_proceso'],
                medio_control=d['medio_control'],
                defaults=d
            )
            if created:
                creados += 1
                self.stdout.write(
                    f'   [+] Creado: #{d["num_proceso"]} - {d["medio_control"]}'
                )
            else:
                self.stdout.write(
                    f'   [=] Ya existe: #{d["num_proceso"]} - {d["medio_control"]}'
                )

        self.stdout.write(self.style.SUCCESS(
            f'   --> {creados} nuevos registros pasivos cargados.'
        ))

    # ------------------------------------------------------------------
    # Usuarios heredados
    # ------------------------------------------------------------------
    def _cargar_usuarios(self):
        self.stdout.write('\n[>] Cargando Usuarios del sistema antiguo...')

        usuarios = [
            {
                'username': 'fvega',
                'nick': 'fvega',
                'email': 'fvega@hosdenar.gov.co',
                'first_name': 'Felipe',
                'last_name': 'Vega',
                'rol': 'administrador',
                'estado': 1,
                'is_staff': True,
                'is_superuser': True,
                'password_plain': 'DefenJur2024!',
            },
            {
                'username': 'arivera',
                'nick': 'arivera',
                'email': 'arivera@hosdenar.gov.co',
                'first_name': 'Andres',
                'last_name': 'Rivera',
                'rol': 'abogado',
                'estado': 1,
                'is_staff': False,
                'is_superuser': False,
                'password_plain': 'DefenJur2024!',
            },
        ]

        creados = 0
        for u in usuarios:
            if Usuario.objects.filter(username=u['username']).exists():
                self.stdout.write(f'   [=] Usuario ya existe: {u["username"]}')
                continue

            user = Usuario.objects.create_user(
                username=u['username'],
                email=u['email'],
                password=u['password_plain'],
                first_name=u['first_name'],
                last_name=u['last_name'],
                nick=u['nick'],
                rol=u['rol'],
                estado=u['estado'],
                is_staff=u['is_staff'],
                is_superuser=u['is_superuser'],
            )
            creados += 1
            self.stdout.write(f'   [+] Creado usuario: {user.username} ({user.rol})')

        self.stdout.write(self.style.SUCCESS(
            f'   --> {creados} nuevos usuarios creados.'
        ))
        if creados > 0:
            self.stdout.write(self.style.WARNING(
                '   [!] Contrasena temporal asignada: DefenJur2024! '
                '-- Solicitar cambio en el primer inicio de sesion.'
            ))
