from rest_framework.response import Response
from rest_framework import status

from ..models import (
    ListaBlancaAdmin, CoordinadorArea, FirmantesFijos,
    DestinatarioRol, PermisoAccesoConfig, SeccionConfig, EncabezadoConfig, CampoConfig,
    CoordinadorAreaGmail,
)
from django.db import connection as _default_conn
from ..permissions import require_roles
from . import APCAPIView as APIView

_ADMIN = require_roles('apc_admin')

# Valores por defecto — se insertan automáticamente la primera vez
_PERMISOS_DEFAULT = [
    ('usuario_dgh',           'Usuario DGH',            True,  1),
    ('correo_institucional',  'Correo Institucional',   True,  2),
    ('carnet',                'Carnet',                 False, 3),
    ('intranet',              'Intranet',               True,  4),
    ('sevenet',               'Sevenet',                True,  5),
    ('mipress',               'Mipress',                True,  6),
    ('ruaf',                  'RUAF',                   True,  7),
    ('vpn_teleconsulta',      'VPN-Teleconsulta',       True,  8),
    ('desprendibles_pago',    'Desprendibles de Pago',  True,  9),
    ('nube_facturacion',      'Nube Facturación',       True,  10),
    ('tarjeta_chip',          'Tarjeta con Chip',       True,  11),
    ('sistema_turnos_recargos','Sistema Turnos y Recargos', True, 12),
    ('mipress_hudn',          'Mipress HUDN',           True,  13),
    ('central_mezclas',       'Central de Mezclas',     True,  14),
    ('utilidades_financieras','Utilidades Financieras', True,  15),
    ('aplicativos_hudn',      'Aplicativos HUDN',       True,  16),
]

_SECCIONES_DEFAULT = [
    (1, 'Datos Personales',                                                      1),
    (2, 'Datos de Vinculación',                                                  2),
    (3, 'Permisos y Accesos Solicitados',                                        3),
    (4, 'Registro de Actividades de Entrenamiento en los Sistemas de Información', 4),
]


def _poblar_permisos():
    """Crea los permisos por defecto si la tabla está vacía."""
    for clave, etiqueta, disp, orden in _PERMISOS_DEFAULT:
        PermisoAccesoConfig.objects.get_or_create(
            clave=clave,
            defaults={'etiqueta': etiqueta, 'disponible_tercerizado': disp, 'orden': orden},
        )


def _poblar_secciones():
    """Crea las secciones por defecto si la tabla está vacía."""
    for numero, titulo, orden in _SECCIONES_DEFAULT:
        SeccionConfig.objects.get_or_create(
            numero=numero,
            defaults={'titulo': titulo, 'orden': orden},
        )


_CAMPOS_DEFAULT = {
    1: [
        ('fecha_diligenciamiento',  'Fecha de diligenciamiento',           1),
        ('num_identificacion',      'Número de identificación',            2),
        ('lugar_expedicion',        'Lugar de expedición',                 3),
        ('nombres_apellidos',       'Nombres y apellidos completos',       4),
        ('direccion_residencia',    'Dirección de residencia',             5),
        ('tel_celular',             'Tel. Celular',                        6),
        ('correo_personal',         'Correo electrónico personal',         7),
        ('tel_fijo',                'Tel. Fijo (opcional)',                8),
    ],
    2: [
        ('tipo_vinculacion',              'Tipo de vinculación',                   1),
        ('op_planta_permanente',          'Opción: Planta Permanente',            2),
        ('op_planta_temporal',            'Opción: Planta Temporal',              3),
        ('op_ops',                        'Opción: OPS',                           4),
        ('op_tercerizado',                'Opción: Tercerizado(a)/Contratista',    5),
        ('periodo_inicio',                'Período — Fecha inicial',               6),
        ('periodo_fin',                   'Período — Fecha final',                 7),
        ('area_servicios',                'Área de servicios',                     8),
        ('cargo_funcionario',             'Cargo del funcionario(a)',              9),
        ('num_registro_tarjeta',          'N° registro o tarjeta profesional',    10),
        ('nombre_empresa_contratista',    'Nombre empresa contratista (si aplica)',11),
        ('direccion_empresa_contratista', 'Dirección empresa contratista',        12),
        ('tel_empresa_contratista',       'Teléfono empresa contratista',         13),
    ],
    4: [
        ('fecha_entrenamiento',          'Fecha de entrenamiento',      1),
        ('hora_inicio_entrenamiento',    'Hora de inicio',              2),
        ('hora_fin_entrenamiento',       'Hora de finalización',        3),
        ('responsable_entrenamiento',    'Responsable de entrenamiento',4),
        ('check_dgh',                    'DGH',                         5),
        ('check_correo_institucional',   'Correo Institucional',        6),
        ('check_aplicativos_hudn',       'Aplicativos HUDN',            7),
        ('check_intranet',               'Intranet',                    8),
    ],
}


def _poblar_campos():
    """Crea los campos por defecto de secciones 1, 2 y 4 si la tabla está vacía."""
    for seccion, campos in _CAMPOS_DEFAULT.items():
        for clave, etiqueta, orden in campos:
            CampoConfig.objects.get_or_create(
                seccion=seccion, campo_clave=clave,
                defaults={'etiqueta': etiqueta, 'orden': orden},
            )


# ── Lista Blanca Admin ────────────────────────────────────────────────────────

class ListaBlancaAdminListView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        qs = ListaBlancaAdmin.objects.order_by('nombre')
        return Response([
            {
                'id': lb.id, 'usunombre': lb.usunombre, 'usuemail': lb.usuemail,
                'nombre': lb.nombre, 'avatar': lb.avatar, 'activo': lb.activo,
                'created_at': str(lb.created_at),
            }
            for lb in qs
        ])

    def post(self, request):
        data = request.data
        for f in ['usunombre', 'usuemail', 'nombre']:
            if not data.get(f):
                return Response({'detail': f'Campo requerido: {f}'}, status=400)
        if ListaBlancaAdmin.objects.filter(usunombre=data['usunombre']).exists():
            return Response({'detail': 'El usuario ya existe'}, status=409)
        lb = ListaBlancaAdmin.objects.create(
            usunombre=data['usunombre'], usuemail=data['usuemail'],
            nombre=data['nombre'],
            avatar=data.get('avatar', (data['nombre'][:2].upper())),
        )
        return Response({'ok': True, 'id': lb.id}, status=201)


class ListaBlancaAdminDetailView(APIView):
    permission_classes = [_ADMIN]

    def patch(self, request, lb_id):
        try:
            lb = ListaBlancaAdmin.objects.get(id=lb_id)
        except ListaBlancaAdmin.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        campos = ['usunombre', 'usuemail', 'nombre', 'avatar', 'activo']
        upd = []
        for c in campos:
            if c in request.data:
                setattr(lb, c, request.data[c])
                upd.append(c)
        if upd:
            lb.save(update_fields=upd)
        return Response({'ok': True})

    def delete(self, request, lb_id):
        try:
            lb = ListaBlancaAdmin.objects.get(id=lb_id)
        except ListaBlancaAdmin.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        if lb.usunombre == request.apc_user.get('usunombre'):
            return Response({'detail': 'No puedes eliminarte a ti mismo'}, status=400)
        lb.delete()
        return Response({'ok': True})


# ── Coordinadores por área ────────────────────────────────────────────────────

class CoordinadorAreaListView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        return Response([
            {
                'id': c.id, 'area_nombre': c.area_nombre,
                'nombre_coordinador': c.nombre_coordinador,
                'email_coordinador': c.email_coordinador, 'activo': c.activo,
            }
            for c in CoordinadorArea.objects.order_by('area_nombre')
        ])

    def post(self, request):
        data = request.data
        for f in ['area_nombre', 'nombre_coordinador', 'email_coordinador']:
            if not data.get(f):
                return Response({'detail': f'Campo requerido: {f}'}, status=400)
        if CoordinadorArea.objects.filter(area_nombre__iexact=data['area_nombre']).exists():
            return Response({'detail': 'El área ya tiene coordinador registrado'}, status=409)
        c = CoordinadorArea.objects.create(
            area_nombre=data['area_nombre'],
            nombre_coordinador=data['nombre_coordinador'],
            email_coordinador=data['email_coordinador'],
        )
        return Response({'ok': True, 'id': c.id}, status=201)


class CoordinadorAreaDetailView(APIView):
    permission_classes = [_ADMIN]

    def patch(self, request, coord_id):
        try:
            c = CoordinadorArea.objects.get(id=coord_id)
        except CoordinadorArea.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        for f in ['area_nombre', 'nombre_coordinador', 'email_coordinador', 'activo']:
            if f in request.data:
                setattr(c, f, request.data[f])
        c.save()
        return Response({'ok': True})

    def delete(self, request, coord_id):
        try:
            CoordinadorArea.objects.get(id=coord_id).delete()
        except CoordinadorArea.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        return Response({'ok': True})


# ── Firmantes fijos ───────────────────────────────────────────────────────────

class FirmantesFijosListView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        return Response([
            {
                'id': f.id, 'rol': f.rol, 'rol_label': f.get_rol_display(),
                'nombre': f.nombre, 'email': f.email, 'activo': f.activo,
            }
            for f in FirmantesFijos.objects.all()
        ])

    def post(self, request):
        data = request.data
        rol = data.get('rol', '')
        if rol not in ('coord_talento_humano', 'coord_gestion_info'):
            return Response({'detail': 'Rol inválido'}, status=400)
        for f in ['nombre', 'email']:
            if not data.get(f):
                return Response({'detail': f'Campo requerido: {f}'}, status=400)
        obj, created = FirmantesFijos.objects.update_or_create(
            rol=rol,
            defaults={'nombre': data['nombre'], 'email': data['email'], 'activo': True},
        )
        return Response({'ok': True, 'id': obj.id}, status=201 if created else 200)


class FirmantesFijosDetailView(APIView):
    permission_classes = [_ADMIN]

    def patch(self, request, fijo_id):
        try:
            f = FirmantesFijos.objects.get(id=fijo_id)
        except FirmantesFijos.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        for campo in ['nombre', 'email', 'activo']:
            if campo in request.data:
                setattr(f, campo, request.data[campo])
        f.save()
        return Response({'ok': True})


# ── Destinatarios por rol ─────────────────────────────────────────────────────

class DestinatarioRolListView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        permiso = request.query_params.get('permiso', None)
        qs = DestinatarioRol.objects.order_by('permiso_clave', 'nombre')
        if permiso:
            qs = qs.filter(permiso_clave=permiso)
        return Response([
            {
                'id': d.id, 'permiso_clave': d.permiso_clave,
                'nombre': d.nombre, 'email': d.email, 'activo': d.activo,
            }
            for d in qs
        ])

    def post(self, request):
        data = request.data
        for f in ['permiso_clave', 'nombre', 'email']:
            if not data.get(f):
                return Response({'detail': f'Campo requerido: {f}'}, status=400)
        d = DestinatarioRol.objects.create(
            permiso_clave=data['permiso_clave'],
            nombre=data['nombre'],
            email=data['email'],
        )
        return Response({'ok': True, 'id': d.id}, status=201)


class DestinatarioRolDetailView(APIView):
    permission_classes = [_ADMIN]

    def patch(self, request, dest_id):
        try:
            d = DestinatarioRol.objects.get(id=dest_id)
        except DestinatarioRol.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        for f in ['permiso_clave', 'nombre', 'email', 'activo']:
            if f in request.data:
                setattr(d, f, request.data[f])
        d.save()
        return Response({'ok': True})

    def delete(self, request, dest_id):
        try:
            DestinatarioRol.objects.get(id=dest_id).delete()
        except DestinatarioRol.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        return Response({'ok': True})


# ── Configuración de permisos del formulario ──────────────────────────────────

class PermisoAccesoConfigListView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        if not PermisoAccesoConfig.objects.exists():
            _poblar_permisos()
        return Response([
            {
                'id': p.id, 'clave': p.clave, 'etiqueta': p.etiqueta,
                'activo': p.activo, 'orden': p.orden,
                'disponible_tercerizado': p.disponible_tercerizado,
            }
            for p in PermisoAccesoConfig.objects.order_by('orden')
        ])

    def post(self, request):
        data = request.data
        for f in ['clave', 'etiqueta']:
            if not data.get(f):
                return Response({'detail': f'Campo requerido: {f}'}, status=400)
        if PermisoAccesoConfig.objects.filter(clave=data['clave']).exists():
            return Response({'detail': 'La clave ya existe'}, status=409)
        p = PermisoAccesoConfig.objects.create(
            clave=data['clave'], etiqueta=data['etiqueta'],
            orden=data.get('orden', 99),
            disponible_tercerizado=data.get('disponible_tercerizado', True),
        )
        return Response({'ok': True, 'id': p.id}, status=201)


class PermisoAccesoConfigDetailView(APIView):
    permission_classes = [_ADMIN]

    def patch(self, request, perm_id):
        try:
            p = PermisoAccesoConfig.objects.get(id=perm_id)
        except PermisoAccesoConfig.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        for f in ['clave', 'etiqueta', 'activo', 'orden', 'disponible_tercerizado']:
            if f in request.data:
                setattr(p, f, request.data[f])
        p.save()
        return Response({'ok': True})

    def delete(self, request, perm_id):
        try:
            PermisoAccesoConfig.objects.get(id=perm_id).delete()
        except PermisoAccesoConfig.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        return Response({'ok': True})


# ── Configuración de secciones ────────────────────────────────────────────────

class SeccionConfigListView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        if not SeccionConfig.objects.exists():
            _poblar_secciones()
        return Response([
            {'id': s.id, 'numero': s.numero, 'titulo': s.titulo, 'activa': s.activa, 'orden': s.orden}
            for s in SeccionConfig.objects.order_by('orden')
        ])

    def post(self, request):
        data = request.data
        for f in ['numero', 'titulo']:
            if not data.get(f) and data.get(f) != 0:
                return Response({'detail': f'Campo requerido: {f}'}, status=400)
        s = SeccionConfig.objects.create(
            numero=data['numero'], titulo=data['titulo'],
            orden=data.get('orden', data['numero']),
        )
        return Response({'ok': True, 'id': s.id}, status=201)


class SeccionConfigDetailView(APIView):
    permission_classes = [_ADMIN]

    def patch(self, request, sec_id):
        try:
            s = SeccionConfig.objects.get(id=sec_id)
        except SeccionConfig.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        for f in ['numero', 'titulo', 'activa', 'orden']:
            if f in request.data:
                setattr(s, f, request.data[f])
        s.save()
        return Response({'ok': True})

    def delete(self, request, sec_id):
        try:
            SeccionConfig.objects.get(id=sec_id).delete()
        except SeccionConfig.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        return Response({'ok': True})


# ── Encabezado ────────────────────────────────────────────────────────────────

class EncabezadoConfigView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        enc, _ = EncabezadoConfig.objects.get_or_create(pk=1)
        return Response({
            'titulo': enc.titulo, 'codigo': enc.codigo, 'version': enc.version,
            'fecha_elaboracion': enc.fecha_elaboracion,
            'fecha_actualizacion': enc.fecha_actualizacion,
            'hoja': enc.hoja,
            'texto_mensaje': enc.texto_mensaje,
        })

    def patch(self, request):
        enc, _ = EncabezadoConfig.objects.get_or_create(pk=1)
        campos = ['titulo', 'codigo', 'version', 'fecha_elaboracion',
                  'fecha_actualizacion', 'hoja', 'texto_mensaje']
        for f in campos:
            if f in request.data:
                setattr(enc, f, request.data[f])
        enc.save()
        return Response({'ok': True})


# ── Campos de secciones 1, 2 y 4 ─────────────────────────────────────────────

class CampoConfigListView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        seccion = request.query_params.get('seccion')
        if not CampoConfig.objects.exists():
            _poblar_campos()
        qs = CampoConfig.objects.order_by('seccion', 'orden')
        if seccion:
            qs = qs.filter(seccion=int(seccion))
        return Response([
            {
                'id': c.id, 'seccion': c.seccion, 'campo_clave': c.campo_clave,
                'etiqueta': c.etiqueta, 'activo': c.activo, 'orden': c.orden,
            }
            for c in qs
        ])


class CampoConfigDetailView(APIView):
    permission_classes = [_ADMIN]

    def patch(self, request, campo_id):
        try:
            c = CampoConfig.objects.get(id=campo_id)
        except CampoConfig.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=404)
        for f in ['etiqueta', 'activo', 'orden']:
            if f in request.data:
                setattr(c, f, request.data[f])
        c.save()
        return Response({'ok': True})


# ── Coordinadores de área desde horas_extras (solo gmail editable) ────────────

class CoordinadorRecargosListView(APIView):
    permission_classes = [_ADMIN]

    def get(self, request):
        # Sincroniza coordinadores desde horas_extras → tabla APC usando raw SQL
        # (igual que AreasView y BuscarFuncionarioView para evitar problemas ORM cross-schema).
        # El gmail guardado en APC nunca se sobreescribe.
        try:
            with _default_conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        cr.id,
                        cr.nombre,
                        STRING_AGG(ar.nombre, ', ')
                            WITHIN GROUP (ORDER BY ar.nombre) AS areas
                    FROM horas_extras_coordinadorrecargos cr
                    LEFT JOIN horas_extras_coordinadorrecargos_areas cra
                        ON cr.id = cra.coordinadorrecargos_id
                    LEFT JOIN horas_extras_arearecargos ar
                        ON cra.arearecargos_id = ar.id
                    GROUP BY cr.id, cr.nombre
                    ORDER BY cr.nombre
                """)
                filas = cur.fetchall()

            for coord_id, nombre, areas_str in filas:
                areas_str = areas_str or ''
                nombre = (nombre or '').strip()
                obj, created = CoordinadorAreaGmail.objects.get_or_create(
                    coordinador_id=coord_id,
                    defaults={'nombre': nombre, 'areas': areas_str, 'gmail': ''},
                )
                if not created and (obj.nombre != nombre or obj.areas != areas_str):
                    obj.nombre = nombre
                    obj.areas = areas_str
                    obj.save(update_fields=['nombre', 'areas'])

        except Exception as exc:
            import traceback
            print(f'[APC COORD SYNC] error al sincronizar coordinadores: {exc}')
            traceback.print_exc()

        # Devuelve siempre desde la tabla APC (aunque el sync haya fallado)
        return Response([
            {
                'id': obj.id,
                'nombre': obj.nombre,
                'areas': obj.areas,
                'gmail': obj.gmail,
                'usuario_dinamica': obj.usuario_dinamica,
            }
            for obj in CoordinadorAreaGmail.objects.order_by('nombre')
        ])


class CoordinadorRecargosDetailView(APIView):
    permission_classes = [_ADMIN]

    def patch(self, request, coord_id):
        print(f'[APC COORD GMAIL] PATCH coord_id={coord_id} data={request.data}')
        try:
            obj = CoordinadorAreaGmail.objects.get(id=coord_id)
        except CoordinadorAreaGmail.DoesNotExist:
            print(f'[APC COORD GMAIL] No encontrado id={coord_id}')
            return Response({'detail': f'Coordinador con id={coord_id} no encontrado en tabla APC'}, status=404)
        nuevo_gmail = request.data.get('gmail', '').strip()
        nuevo_usuario = request.data.get('usuario_dinamica', '').strip()
        obj.gmail = nuevo_gmail
        obj.usuario_dinamica = nuevo_usuario
        obj.save(update_fields=['gmail', 'usuario_dinamica'])
        print(f'[APC COORD GMAIL] OK guardado gmail={nuevo_gmail} usuario_dinamica={nuevo_usuario} para coord_id={coord_id}')
        return Response({'ok': True})
