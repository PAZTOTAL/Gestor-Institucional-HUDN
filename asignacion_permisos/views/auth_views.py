import hashlib
import base64

import pyodbc
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

from ..auth import create_token
from ..models import ListaBlancaAdmin, CoordinadorAreaGmail
from ..permissions import IsAuthenticated
from . import APCAPIView as APIView


def _md5_vbnet(password: str) -> str:
    raw = password.encode('utf-16-le')
    digest = hashlib.md5(raw).digest()
    return base64.b64encode(digest).decode('ascii')


def _nexus_conn():
    server = settings.DATABASES['default']['HOST']
    db_name = getattr(settings, 'PYS_DB_NEXUS_NAME', 'DGEMPRES_NEXUS')
    user = getattr(settings, 'PYS_DB_NEXUS_USER', '')
    password = getattr(settings, 'PYS_DB_NEXUS_PASS', '')
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server},1433;DATABASE={db_name};"
        f"UID={user};PWD={password};"
        f"TrustServerCertificate=yes;Connection Timeout=5;"
    )
    return pyodbc.connect(conn_str, timeout=5)


class LoginAdminView(APIView):
    """Login para administradores del módulo APC."""
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

        clave_hash = _md5_vbnet(usuclave)

        try:
            conn = _nexus_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT USUNOMBRE, USUCLAVE, USUEMAIL, USUDESCRI FROM genusuario WHERE USUNOMBRE = ?",
                usunombre,
            )
            row = cursor.fetchone()
            conn.close()
        except Exception as e:
            return Response(
                {'detail': f'Error conectando al servidor: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not row or row.USUCLAVE != clave_hash:
            return Response(
                {'detail': 'Usuario o contraseña incorrectos'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        usudescri = (row.USUDESCRI or '').strip()

        # Verificar si es administrador
        lb = ListaBlancaAdmin.objects.filter(usunombre=usunombre, activo=True).first()
        if lb:
            token = create_token({
                'usunombre': lb.usunombre,
                'usuemail': lb.usuemail,
                'nombre': lb.nombre,
                'nombre_completo': usudescri,
                'rol': 'apc_admin',
            })
            return Response({
                'token': token,
                'user': {
                    'usunombre': lb.usunombre,
                    'usuemail': lb.usuemail,
                    'nombre': lb.nombre,
                    'nombreCompleto': usudescri,
                    'rol': 'apc_admin',
                },
            })

        # Verificar si es coordinador de área (usuario_dinamica)
        coord = CoordinadorAreaGmail.objects.filter(
            usuario_dinamica=usunombre
        ).first()
        if coord:
            token = create_token({
                'usunombre': usunombre,
                'usuemail': coord.gmail,
                'nombre': coord.nombre,
                'nombre_completo': usudescri,
                'rol': 'coord_area',
                'coord_id': coord.id,
                'coord_areas': coord.areas,
            })
            return Response({
                'token': token,
                'user': {
                    'usunombre': usunombre,
                    'usuemail': coord.gmail,
                    'nombre': coord.nombre,
                    'nombreCompleto': usudescri,
                    'rol': 'coord_area',
                },
            })

        return Response(
            {'detail': 'Usuario no autorizado para acceder a este módulo'},
            status=status.HTTP_403_FORBIDDEN,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(request.apc_user)
