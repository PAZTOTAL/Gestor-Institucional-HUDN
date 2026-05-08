import pyodbc
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..auth import md5_vbnet, create_token, decode_token
from ..models import ListaBlanca, LogAcceso, UsuarioApp
from ..permissions import IsAuthenticated


def _get_nexus_connection():
    server = settings.DATABASES['default']['HOST']
    db_name = getattr(settings, 'PYS_DB_NEXUS_NAME', 'DGEMPRES_NEXUS')
    user = getattr(settings, 'PYS_DB_NEXUS_USER', '')
    password = getattr(settings, 'PYS_DB_NEXUS_PASS', '')
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server},1433;"
        f"DATABASE={db_name};"
        f"UID={user};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=5;"
    )
    return pyodbc.connect(conn_str, timeout=5)


class LoginView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        usunombre = request.data.get('usunombre', '').strip()
        usuclave = request.data.get('usuclave', '')

        if not usunombre or not usuclave:
            return Response(
                {'detail': 'Usuario y contraseña son requeridos'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clave_hash = md5_vbnet(usuclave)

        # 1. Verificar en SQL Server (genusuario)
        try:
            conn = _get_nexus_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT USUNOMBRE, USUCLAVE, USUEMAIL, USUDESCRI FROM genusuario WHERE USUNOMBRE = ?",
                usunombre,
            )
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            return Response(
                {'detail': f'No se pudo conectar al servidor principal: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not row:
            return Response(
                {'detail': 'Usuario no encontrado en el sistema'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if row.USUCLAVE != clave_hash:
            return Response(
                {'detail': 'Usuario o contraseña incorrectos'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 2. Verificar lista blanca
        try:
            lb = (
                ListaBlanca.objects
                .select_related('area')
                .get(usunombre=usunombre, activo=True)
            )
        except ListaBlanca.DoesNotExist:
            return Response(
                {'detail': 'Usuario no autorizado para usar esta aplicación'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 3. Registrar acceso y actualizar usuarios_app
        ip = request.META.get('REMOTE_ADDR')
        LogAcceso.objects.create(
            usunombre=lb.usunombre,
            nombre=lb.nombre,
            rol=lb.rol,
            accion='LOGIN',
            ip=ip,
        )
        UsuarioApp.objects.update_or_create(
            usunombre=lb.usunombre,
            defaults={
                'nombre_completo': lb.nombre,
                'ultimo_login': timezone.now(),
            },
        )

        # 4. Emitir JWT
        usudescri = (row.USUDESCRI or '').strip()
        token = create_token({
            'usunombre': lb.usunombre,
            'usuemail': lb.usuemail,
            'nombre': lb.nombre,
            'nombre_completo': usudescri,
            'avatar': lb.avatar,
            'rol': lb.rol,
            'area_id': lb.area_id,
            'area_nombre': lb.area.nombre if lb.area else None,
            'area_orden': lb.area.orden if lb.area else None,
        })

        return Response({
            'token': token,
            'user': {
                'usunombre': lb.usunombre,
                'usuemail': lb.usuemail,
                'nombre': lb.nombre,
                'nombreCompleto': usudescri,
                'avatar': lb.avatar,
                'rol': lb.rol,
                'areaId': lb.area_id,
                'areaNombre': lb.area.nombre if lb.area else None,
                'areaOrden': lb.area.orden if lb.area else None,
            },
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.pys_user
        ip = request.META.get('REMOTE_ADDR')
        LogAcceso.objects.create(
            usunombre=user['usunombre'],
            nombre=user.get('nombre', ''),
            rol=user.get('rol', ''),
            accion='LOGOUT',
            ip=ip,
        )
        return Response({'ok': True})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(request.pys_user)
