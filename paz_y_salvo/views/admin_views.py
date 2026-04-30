import pyodbc
from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status

from ..models import ListaBlanca, Area, FirmanteConfig
from ..permissions import require_roles
from . import PysAPIView as APIView

ROLES_VALIDOS = ('paz_salvo', 'permisos', 'validador', 'firmador', 'admin')


class ListaBlancaListCreateView(APIView):
    permission_classes = [require_roles('admin')]

    def get(self, request):
        qs = ListaBlanca.objects.select_related('area').order_by('rol', 'nombre')
        result = []
        for lb in qs:
            result.append({
                'id': lb.id,
                'usunombre': lb.usunombre,
                'usuemail': lb.usuemail,
                'nombre': lb.nombre,
                'avatar': lb.avatar,
                'rol': lb.rol,
                'area_id': lb.area_id,
                'area_nombre': lb.area.nombre if lb.area else None,
                'activo': lb.activo,
                'created_at': str(lb.created_at),
            })
        return Response(result)

    def post(self, request):
        data = request.data
        rol = data.get('rol')
        if rol not in ROLES_VALIDOS:
            return Response(
                {'detail': f'Rol inválido. Válidos: {", ".join(ROLES_VALIDOS)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        required = ['usunombre', 'usuemail', 'nombre']
        for f in required:
            if not data.get(f):
                return Response({'detail': f'Campo requerido: {f}'}, status=status.HTTP_400_BAD_REQUEST)

        if ListaBlanca.objects.filter(usunombre=data['usunombre']).exists():
            return Response({'detail': 'El usuario ya existe en la lista blanca'}, status=status.HTTP_409_CONFLICT)

        lb = ListaBlanca.objects.create(
            usunombre=data['usunombre'],
            usuemail=data['usuemail'],
            nombre=data['nombre'],
            avatar=data.get('avatar', 'US'),
            rol=rol,
            area_id=data.get('area_id'),
        )
        return Response({'ok': True, 'id': lb.id}, status=status.HTTP_201_CREATED)


class ListaBlancaDetailView(APIView):
    permission_classes = [require_roles('admin')]

    def patch(self, request, lb_id):
        try:
            lb = ListaBlanca.objects.get(id=lb_id)
        except ListaBlanca.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        if 'rol' in data and data['rol'] not in ROLES_VALIDOS:
            return Response({'detail': f'Rol inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        campos = ['usunombre', 'usuemail', 'nombre', 'avatar', 'rol', 'area_id', 'activo']
        updated = []
        for campo in campos:
            if campo in data:
                setattr(lb, campo, data[campo])
                updated.append(campo)

        if not updated:
            return Response({'detail': 'Sin cambios'}, status=status.HTTP_400_BAD_REQUEST)

        lb.save(update_fields=updated)
        return Response({'ok': True})

    def delete(self, request, lb_id):
        user = request.pys_user
        try:
            lb = ListaBlanca.objects.get(id=lb_id)
        except ListaBlanca.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)
        if lb.usunombre == user.get('usunombre'):
            return Response({'detail': 'No puedes eliminarte a ti mismo'}, status=status.HTTP_400_BAD_REQUEST)
        lb.delete()
        return Response({'ok': True})


class AreaListView(APIView):
    permission_classes = [require_roles('admin')]

    def get(self, request):
        areas = Area.objects.all()
        return Response([
            {'id': a.id, 'nombre': a.nombre, 'responsable': a.responsable, 'orden': a.orden, 'activa': a.activa}
            for a in areas
        ])


class AreaDetailView(APIView):
    permission_classes = [require_roles('admin')]

    def patch(self, request, area_id):
        try:
            area = Area.objects.get(id=area_id)
        except Area.DoesNotExist:
            return Response({'detail': 'No encontrada'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        campos = ['nombre', 'responsable', 'activa', 'orden']
        updated = []
        for campo in campos:
            if campo in data:
                setattr(area, campo, data[campo])
                updated.append(campo)

        if not updated:
            return Response({'detail': 'Sin cambios'}, status=status.HTTP_400_BAD_REQUEST)

        area.save(update_fields=updated)
        return Response({'ok': True})


class FirmanteConfigListCreateView(APIView):
    permission_classes = [require_roles('admin')]

    def get(self, request):
        qs = FirmanteConfig.objects.select_related('lb').order_by('orden')
        return Response([
            {
                'id': fc.id,
                'lb_id': fc.lb_id,
                'rol_label': fc.rol_label,
                'orden': fc.orden,
                'activo': fc.activo,
                'nombre': fc.lb.nombre,
                'usunombre': fc.lb.usunombre,
                'usuemail': fc.lb.usuemail,
                'avatar': fc.lb.avatar,
            }
            for fc in qs
        ])

    def post(self, request):
        data = request.data
        lb_id = data.get('lb_id')
        rol_label = data.get('rol_label')
        orden = data.get('orden')

        if not lb_id or not rol_label or orden is None:
            return Response({'detail': 'lb_id, rol_label y orden son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lb = ListaBlanca.objects.get(id=lb_id)
        except ListaBlanca.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if FirmanteConfig.objects.filter(lb=lb, rol_label=rol_label).exists():
            return Response({'detail': 'Este usuario ya está como firmante'}, status=status.HTTP_409_CONFLICT)

        fc = FirmanteConfig.objects.create(lb=lb, rol_label=rol_label, orden=orden)
        return Response({'ok': True, 'id': fc.id}, status=status.HTTP_201_CREATED)


class FirmanteConfigDetailView(APIView):
    permission_classes = [require_roles('admin')]

    def patch(self, request, cfg_id):
        try:
            fc = FirmanteConfig.objects.get(id=cfg_id)
        except FirmanteConfig.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        campos = ['lb_id', 'rol_label', 'orden', 'activo']
        updated = []
        for campo in campos:
            if campo in data:
                setattr(fc, campo, data[campo])
                updated.append(campo)

        if updated:
            fc.save(update_fields=updated)
        return Response({'ok': True})

    def delete(self, request, cfg_id):
        try:
            fc = FirmanteConfig.objects.get(id=cfg_id)
        except FirmanteConfig.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)
        fc.delete()
        return Response({'ok': True})


# ── Catálogos desde SQL Server ─────────────────────────────────────────────────

def _query_sqlserver(db_name: str, sql: str) -> list:
    server = settings.DATABASES['default']['HOST']
    nexus_user = getattr(settings, 'PYS_DB_NEXUS_USER', '')
    nexus_pass = getattr(settings, 'PYS_DB_NEXUS_PASS', '')
    sgc_user = getattr(settings, 'PYS_DB_SGC_USER', nexus_user)
    sgc_pass = getattr(settings, 'PYS_DB_SGC_PASS', nexus_pass)

    is_sgc = db_name == getattr(settings, 'PYS_DB_SGC_NAME', 'SGC_HUDN')
    user = sgc_user if is_sgc else nexus_user
    password = sgc_pass if is_sgc else nexus_pass

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server},1433;DATABASE={db_name};"
        f"UID={user};PWD={password};"
        f"TrustServerCertificate=yes;Connection Timeout=5;"
    )
    with pyodbc.connect(conn_str, timeout=5) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


class CatalogoCargosView(APIView):
    permission_classes = [require_roles('paz_salvo', 'permisos', 'admin')]

    def get(self, request):
        cached = cache.get('pys_cat_cargos')
        if cached is not None:
            return Response(cached)
        db_name = getattr(settings, 'PYS_DB_NEXUS_NAME', 'DGEMPRES_NEXUS')
        try:
            rows = _query_sqlserver(db_name, "SELECT GCANOMBRE FROM GENCARGO ORDER BY GCANOMBRE")
            result = [r['GCANOMBRE'].strip() for r in rows if r.get('GCANOMBRE')]
            cache.set('pys_cat_cargos', result, 600)
            return Response(result)
        except Exception as e:
            return Response({'detail': f'Error consultando cargos: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CatalogoDependenciasView(APIView):
    permission_classes = [require_roles('paz_salvo', 'permisos', 'admin')]

    def get(self, request):
        cached = cache.get('pys_cat_dependencias')
        if cached is not None:
            return Response(cached)
        db_name = getattr(settings, 'PYS_DB_SGC_NAME', 'SGC_HUDN')
        try:
            rows = _query_sqlserver(db_name, "SELECT dependencia FROM JurDependencia ORDER BY dependencia")
            result = [r['dependencia'].strip() for r in rows if r.get('dependencia')]
            cache.set('pys_cat_dependencias', result, 600)
            return Response(result)
        except Exception as e:
            return Response({'detail': f'Error consultando dependencias: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CatalogoCoordinadoresView(APIView):
    permission_classes = [require_roles('paz_salvo', 'permisos', 'admin')]

    def get(self, request):
        cached = cache.get('pys_cat_coordinadores')
        if cached is not None:
            return Response(cached)
        db_name = getattr(settings, 'PYS_DB_SGC_NAME', 'SGC_HUDN')
        try:
            rows = _query_sqlserver(
                db_name,
                "SELECT DISTINCT nombre_usuario FROM jur_correos_firmas WHERE nombre_usuario IS NOT NULL ORDER BY nombre_usuario"
            )
            result = [r['nombre_usuario'].strip() for r in rows if r.get('nombre_usuario')]
            cache.set('pys_cat_coordinadores', result, 600)
            return Response(result)
        except Exception as e:
            return Response({'detail': f'Error consultando coordinadores: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BuscarFuncionarioPYSView(APIView):
    """Busca nombre, cargo, dependencia y coordinador por cédula usando horas_extras. Público."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from django.db import connection
        from horas_extras.models import TrabajadorRecargos

        cedula = request.query_params.get('cedula', '').strip()
        if not cedula or not cedula.isdigit():
            return Response({'found': False, 'detail': 'Cédula inválida'}, status=status.HTTP_400_BAD_REQUEST)

        trab = (
            TrabajadorRecargos.objects
            .filter(documento=cedula)
            .select_related('area')
            .first()
        )

        if not trab:
            return Response({'found': False})

        nombre      = trab.nombre.strip()
        cargo       = trab.cargo.strip()
        dependencia = trab.area.nombre.strip() if trab.area else ''
        coordinador = ''
        coordinadores_lista = []

        # Coordinador desde horas_extras_coordinadorrecargos (tabla existente, sin modelo ORM activo)
        if trab.area:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT cr.nombre
                        FROM horas_extras_coordinadorrecargos cr
                        JOIN horas_extras_coordinadorrecargos_areas cra
                          ON cr.id = cra.coordinadorrecargos_id
                        WHERE cra.arearecargos_id = %s
                    """, [trab.area.id])
                    row = cursor.fetchone()
                    if row:
                        coordinador = row[0].strip()
            except Exception as e:
                print(f'[PYS BUSCAR FUNC] Error coordinador: {e}')

        # Si no hay coordinador para el área, devolver todos para que el usuario elija
        if not coordinador:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT nombre FROM horas_extras_coordinadorrecargos
                        WHERE nombre IS NOT NULL AND nombre != ''
                        ORDER BY nombre
                    """)
                    coordinadores_lista = [
                        r[0].strip() for r in cursor.fetchall() if r[0] and r[0].strip()
                    ]
            except Exception as e:
                print(f'[PYS BUSCAR FUNC] Error lista coordinadores: {e}')

        return Response({
            'found': True,
            'nombre': nombre,
            'cargo': cargo,
            'dependencia': dependencia,
            'coordinador': coordinador,
            'coordinadores_lista': coordinadores_lista,
        })
