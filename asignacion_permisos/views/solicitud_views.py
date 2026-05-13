import threading
from django.db import connection
from rest_framework.response import Response
from rest_framework import status

from ..models import (
    SolicitudAPC, PermisoSolicitado, FirmaAPC,
    CoordinadorArea, FirmantesFijos, PermisoAccesoConfig, SeccionConfig,
)
from ..permissions import IsAuthenticated, require_roles
from . import APCAPIView as APIView

# Permisos por defecto si la tabla está vacía
_PERMISOS_DEFAULT = [
    ('usuario_dgh', 'Usuario DGH', True),
    ('correo_institucional', 'Correo Institucional', True),
    ('carnet', 'Carnet', False),  # disponible_tercerizado=False
    ('intranet', 'Intranet', True),
    ('sevenet', 'Sevenet', True),
    ('mipress', 'Mipress', True),
    ('ruaf', 'RUAF', True),
    ('vpn_teleconsulta', 'VPN-Teleconsulta', True),
    ('desprendibles_pago', 'Desprendibles de Pago', True),
    ('nube_facturacion', 'Nube Facturación', True),
    ('tarjeta_chip', 'Tarjeta con Chip', True),
    ('sistema_turnos_recargos', 'Sistema Turnos y Recargos', True),
    ('mipress_hudn', 'Mipress HUDN', True),
    ('central_mezclas', 'Central de Mezclas', True),
    ('utilidades_financieras', 'Utilidades Financieras', True),
    ('aplicativos_hudn', 'Aplicativos HUDN', True),
]

_SECCIONES_DEFAULT = [
    (1, 'Datos Personales'),
    (2, 'Datos de Vinculación'),
    (3, 'Permisos y Accesos Solicitados'),
    (4, 'Registro de Actividades de Entrenamiento en los Sistemas de Información'),
]


class ConfigPermisosView(APIView):
    """Retorna la lista de permisos configurables (Sección 3). Público."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        qs = list(PermisoAccesoConfig.objects.filter(activo=True).order_by('orden'))
        if not qs:
            return Response([
                {'clave': c, 'etiqueta': e, 'disponible_tercerizado': d}
                for c, e, d in _PERMISOS_DEFAULT
            ])
        return Response([
            {
                'clave': p.clave,
                'etiqueta': p.etiqueta,
                'disponible_tercerizado': p.disponible_tercerizado,
            }
            for p in qs
        ])


class ConfigSeccionesView(APIView):
    """Retorna la configuración de secciones del formulario. Público."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        qs = list(SeccionConfig.objects.filter(activa=True).order_by('orden'))
        if not qs:
            return Response([
                {'numero': n, 'titulo': t} for n, t in _SECCIONES_DEFAULT
            ])
        return Response([
            {'numero': s.numero, 'titulo': s.titulo} for s in qs
        ])


class EmpresasTercerizadasView(APIView):
    """Lista de empresas tercerizadas activas. Público."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, razon_social, email_persona_cargo, firma_responsable,
                           direccion, telefono
                    FROM terc_empresa_tercerizada
                    WHERE activa = 1
                    ORDER BY razon_social
                """)
                rows = cursor.fetchall()
            return Response([
                {
                    'id': r[0],
                    'razon_social': r[1],
                    'email_persona_cargo': r[2] or '',
                    'firma_responsable': r[3] or '',
                    'direccion': r[4] or '',
                    'telefono': r[5] or '',
                }
                for r in rows
            ])
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AreasView(APIView):
    """Lista de áreas disponibles (de horas_extras). Público."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, nombre FROM horas_extras_arearecargos ORDER BY nombre"
                )
                rows = cursor.fetchall()
            return Response([{'id': r[0], 'nombre': r[1]} for r in rows])
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BuscarCargosView(APIView):
    """Busca cargos únicos por texto en horas_extras_trabajadorrecargos. Público."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from horas_extras.models import TrabajadorRecargos

        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response([])

        cargos = (
            TrabajadorRecargos.objects
            .filter(cargo__icontains=q)
            .exclude(cargo__isnull=True)
            .exclude(cargo='')
            .values_list('cargo', flat=True)
            .distinct()
            .order_by('cargo')[:12]
        )
        return Response(sorted({c.strip() for c in cargos if c and c.strip()}))


class BuscarFuncionarioView(APIView):
    """Busca datos del funcionario por cédula. Público."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from horas_extras.models import TrabajadorRecargos

        cedula = request.query_params.get('cedula', '').strip()
        if not cedula or not cedula.isdigit():
            return Response({'found': False, 'detail': 'Cédula inválida'},
                            status=status.HTTP_400_BAD_REQUEST)

        trab = (
            TrabajadorRecargos.objects
            .filter(documento=cedula)
            .select_related('area')
            .first()
        )

        if not trab:
            return Response({'found': False})

        coordinador = ''
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT cr.nombre
                    FROM horas_extras_coordinadorrecargos cr
                    JOIN horas_extras_coordinadorrecargos_areas cra
                      ON cr.id = cra.coordinadorrecargos_id
                    WHERE cra.arearecargos_id = %s
                """, [trab.area_id])
                row = cursor.fetchone()
                if row:
                    coordinador = row[0].strip()
        except Exception:
            pass

        return Response({
            'found': True,
            'nombre': trab.nombre.strip(),
            'cargo': (trab.cargo or '').strip(),
            'area': trab.area.nombre.strip() if trab.area else '',
            'coordinador': coordinador,
        })


class SolicitudListView(APIView):
    """Lista de solicitudes — solo admin."""
    permission_classes = [require_roles('apc_admin')]

    def get(self, request):
        qs = SolicitudAPC.objects.prefetch_related('permisos_solicitados', 'firmas').order_by('-fecha_creacion')
        result = []
        for s in qs:
            firmas_info = [
                {
                    'tipo': f.tipo_firma,
                    'tipo_label': f.get_tipo_firma_display(),
                    'nombre': f.nombre_firmante,
                    'firmado': f.firmado,
                    'fecha': str(f.fecha_firma) if f.fecha_firma else None,
                }
                for f in s.firmas.all()
            ]
            result.append({
                'id': s.id,
                'nombres_apellidos': s.nombres_apellidos,
                'num_identificacion': s.num_identificacion,
                'area_servicios': s.area_servicios,
                'cargo_funcionario': s.cargo_funcionario,
                'numero_contrato': s.numero_contrato,
                'tipo_vinculacion': s.tipo_vinculacion,
                'tipo_vinculacion_label': s.get_tipo_vinculacion_display(),
                'periodo_inicio': str(s.periodo_inicio),
                'periodo_fin': str(s.periodo_fin),
                'foto_carnet': s.foto_carnet,
                'tipo_sangre': s.tipo_sangre,
                'estado': s.estado,
                'fecha_creacion': str(s.fecha_creacion),
                'permisos': [p.permiso_clave for p in s.permisos_solicitados.all()],
                'firmas': firmas_info,
            })
        return Response(result)


class SolicitudCreateView(APIView):
    """Crea una nueva solicitud APC. Público (funciona sin login)."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        data = request.data

        # Validaciones básicas
        required = [
            'fecha_diligenciamiento', 'num_identificacion', 'lugar_expedicion',
            'nombres_apellidos', 'direccion_residencia', 'tel_celular',
            'correo_personal', 'tipo_vinculacion', 'periodo_inicio', 'periodo_fin',
            'area_servicios', 'cargo_funcionario',
        ]
        for f in required:
            val = data.get(f, '')
            if not val and val != 0:
                return Response(
                    {'detail': f'Campo requerido: {f}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        num_id = data.get('num_identificacion', '')
        if not str(num_id).isdigit():
            return Response(
                {'detail': 'El número de identificación debe contener solo dígitos'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tipo_vinc = data.get('tipo_vinculacion', '')
        if tipo_vinc not in ('planta_permanente', 'planta_temporal', 'ops', 'tercerizado'):
            return Response(
                {'detail': 'Tipo de vinculación inválido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not data.get('acepto_confidencialidad'):
            return Response(
                {'detail': 'Debe aceptar el acuerdo de confidencialidad'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not data.get('firma_funcionario'):
            return Response(
                {'detail': 'La firma del solicitante es obligatoria'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Crear solicitud
        solicitud = SolicitudAPC.objects.create(
            fecha_diligenciamiento=data['fecha_diligenciamiento'],
            num_identificacion=data['num_identificacion'],
            lugar_expedicion=data['lugar_expedicion'],
            nombres_apellidos=data['nombres_apellidos'],
            direccion_residencia=data['direccion_residencia'],
            tel_celular=data['tel_celular'],
            correo_personal=data['correo_personal'],
            tel_fijo=data.get('tel_fijo', ''),
            tipo_vinculacion=tipo_vinc,
            periodo_inicio=data['periodo_inicio'],
            periodo_fin=data['periodo_fin'],
            area_servicios=data['area_servicios'],
            cargo_funcionario=data['cargo_funcionario'],
            numero_contrato=data.get('numero_contrato', ''),
            num_registro_tarjeta=data.get('num_registro_tarjeta', ''),
            nombre_empresa_contratista=data.get('nombre_empresa_contratista', ''),
            direccion_empresa_contratista=data.get('direccion_empresa_contratista', ''),
            tel_empresa_contratista=data.get('tel_empresa_contratista', ''),
            empresa_tercerizada_id=data.get('empresa_tercerizada_id') or None,
            fecha_entrenamiento=data.get('fecha_entrenamiento') or None,
            hora_inicio_entrenamiento=data.get('hora_inicio_entrenamiento') or None,
            hora_fin_entrenamiento=data.get('hora_fin_entrenamiento') or None,
            responsable_entrenamiento=data.get('responsable_entrenamiento', ''),
            entrenamiento_dgh=bool(data.get('entrenamiento_dgh', False)),
            entrenamiento_correo=bool(data.get('entrenamiento_correo', False)),
            entrenamiento_aplicativos=bool(data.get('entrenamiento_aplicativos', False)),
            entrenamiento_intranet=bool(data.get('entrenamiento_intranet', False)),
            acepto_confidencialidad=True,
            firma_funcionario=data.get('firma_funcionario', ''),
            foto_carnet=data.get('foto_carnet', ''),
            tipo_sangre=data.get('tipo_sangre', ''),
            creado_por=data.get('creado_por', ''),
            correo_notificacion=data.get('correo_personal', ''),
        )

        # Permisos solicitados
        permisos_claves = data.get('permisos', [])
        if isinstance(permisos_claves, list):
            # Tercerizado no puede pedir carnet
            if tipo_vinc == 'tercerizado' and 'carnet' in permisos_claves:
                permisos_claves = [p for p in permisos_claves if p != 'carnet']
            for clave in permisos_claves:
                if clave:
                    PermisoSolicitado.objects.create(
                        solicitud=solicitud, permiso_clave=clave
                    )

        # Crear firma del funcionario (ya firmada)
        FirmaAPC.objects.create(
            solicitud=solicitud,
            tipo_firma='funcionario',
            nombre_firmante=solicitud.nombres_apellidos,
            email_firmante=solicitud.correo_personal,
            firma_imagen=solicitud.firma_funcionario,
            firmado=True,
            orden=0,
        )

        # Crear firmas pendientes y enviar correos en hilo secundario
        threading.Thread(
            target=_crear_firmas_y_enviar,
            args=(solicitud.id,),
            daemon=True,
        ).start()

        return Response(
            {'ok': True, 'id': solicitud.id,
             'mensaje': 'Solicitud enviada correctamente. Los responsables recibirán un correo para firmar.'},
            status=status.HTTP_201_CREATED,
        )


class SolicitudDetailView(APIView):
    permission_classes = [require_roles('apc_admin')]

    def get(self, request, sol_id):
        try:
            s = SolicitudAPC.objects.prefetch_related('permisos_solicitados', 'firmas').get(id=sol_id)
        except SolicitudAPC.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)

        return Response(_serializar_solicitud(s))

    def patch(self, request, sol_id):
        try:
            s = SolicitudAPC.objects.get(id=sol_id)
        except SolicitudAPC.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)
        nuevo_estado = request.data.get('estado')
        if nuevo_estado in ('EN_TRAMITE', 'COMPLETADO', 'RECHAZADO'):
            s.estado = nuevo_estado
            s.save(update_fields=['estado'])
        return Response({'ok': True})


def _serializar_solicitud(s: SolicitudAPC) -> dict:
    firmas = [
        {
            'id': f.id,
            'tipo': f.tipo_firma,
            'tipo_label': f.get_tipo_firma_display(),
            'nombre': f.nombre_firmante,
            'email': f.email_firmante,
            'firmado': f.firmado,
            'fecha': str(f.fecha_firma) if f.fecha_firma else None,
            'orden': f.orden,
        }
        for f in s.firmas.all()
    ]
    return {
        'id': s.id,
        'fecha_diligenciamiento': str(s.fecha_diligenciamiento),
        'num_identificacion': s.num_identificacion,
        'lugar_expedicion': s.lugar_expedicion,
        'nombres_apellidos': s.nombres_apellidos,
        'direccion_residencia': s.direccion_residencia,
        'tel_celular': s.tel_celular,
        'correo_personal': s.correo_personal,
        'tel_fijo': s.tel_fijo,
        'tipo_vinculacion': s.tipo_vinculacion,
        'tipo_vinculacion_label': s.get_tipo_vinculacion_display(),
        'periodo_inicio': str(s.periodo_inicio),
        'periodo_fin': str(s.periodo_fin),
        'area_servicios': s.area_servicios,
        'cargo_funcionario': s.cargo_funcionario,
        'numero_contrato': s.numero_contrato,
        'num_registro_tarjeta': s.num_registro_tarjeta,
        'nombre_empresa_contratista': s.nombre_empresa_contratista,
        'direccion_empresa_contratista': s.direccion_empresa_contratista,
        'tel_empresa_contratista': s.tel_empresa_contratista,
        'fecha_entrenamiento': str(s.fecha_entrenamiento) if s.fecha_entrenamiento else None,
        'hora_inicio_entrenamiento': str(s.hora_inicio_entrenamiento) if s.hora_inicio_entrenamiento else None,
        'hora_fin_entrenamiento': str(s.hora_fin_entrenamiento) if s.hora_fin_entrenamiento else None,
        'responsable_entrenamiento': s.responsable_entrenamiento,
        'entrenamiento_dgh': s.entrenamiento_dgh,
        'entrenamiento_correo': s.entrenamiento_correo,
        'entrenamiento_aplicativos': s.entrenamiento_aplicativos,
        'entrenamiento_intranet': s.entrenamiento_intranet,
        'firma_funcionario': s.firma_funcionario,
        'foto_carnet': s.foto_carnet,
        'tipo_sangre': s.tipo_sangre,
        'estado': s.estado,
        'fecha_creacion': str(s.fecha_creacion),
        'permisos': [p.permiso_clave for p in s.permisos_solicitados.all()],
        'firmas': firmas,
    }


def _crear_firmas_y_enviar(solicitud_id: int):
    from django.db import close_old_connections
    from ..email_service import enviar_correos_firma

    close_old_connections()
    try:
        solicitud = SolicitudAPC.objects.get(id=solicitud_id)
        es_tercerizado = solicitud.es_tercerizado
        area = solicitud.area_servicios

        # Buscar coordinador del área en la tabla APC (apc_coordinador_area_gmail)
        # que está sincronizada desde horas_extras y tiene el gmail editable.
        coord_nombre = 'Coordinador de Área'
        coord_email = ''
        try:
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT cag.nombre, cag.gmail
                    FROM apc_coordinador_area_gmail cag
                    INNER JOIN horas_extras_coordinadorrecargos_areas cra
                        ON cag.coordinador_id = cra.coordinadorrecargos_id
                    INNER JOIN horas_extras_arearecargos ar
                        ON cra.arearecargos_id = ar.id
                    WHERE ar.nombre = %s AND cag.gmail != ''
                """, [area])
                row = cur.fetchone()
            if row:
                coord_nombre, coord_email = row[0].strip(), row[1].strip()
            else:
                # Fallback: buscar solo por nombre (sin gmail)
                with connection.cursor() as cur:
                    cur.execute("""
                        SELECT cag.nombre
                        FROM apc_coordinador_area_gmail cag
                        INNER JOIN horas_extras_coordinadorrecargos_areas cra
                            ON cag.coordinador_id = cra.coordinadorrecargos_id
                        INNER JOIN horas_extras_arearecargos ar
                            ON cra.arearecargos_id = ar.id
                        WHERE ar.nombre = %s
                    """, [area])
                    row2 = cur.fetchone()
                if row2:
                    coord_nombre = row2[0].strip()
        except Exception as e:
            print(f'[APC] Error buscando coordinador para área "{area}": {e}')

        # Firmante 1: coordinador de área (orden=1)
        firma_coord = FirmaAPC.objects.create(
            solicitud=solicitud,
            tipo_firma='coordinador_area',
            nombre_firmante=coord_nombre,
            email_firmante=coord_email,
            orden=1,
        )

        # Firmante 2: responsable contratista (orden=1)
        if es_tercerizado:
            resp_nombre = solicitud.nombre_empresa_contratista or 'Responsable Contratista'
            resp_email = ''
            resp_firma = ''
            if solicitud.empresa_tercerizada_id:
                try:
                    with connection.cursor() as cur:
                        cur.execute("""
                            SELECT razon_social, email_persona_cargo, firma_responsable
                            FROM terc_empresa_tercerizada
                            WHERE id = %s
                        """, [solicitud.empresa_tercerizada_id])
                        row = cur.fetchone()
                    if row:
                        resp_nombre = row[0] or resp_nombre
                        resp_email = row[1] or ''
                        resp_firma = row[2] or ''
                except Exception as e:
                    print(f'[APC] Error buscando empresa tercerizada id={solicitud.empresa_tercerizada_id}: {e}')
            FirmaAPC.objects.create(
                solicitud=solicitud,
                tipo_firma='resp_contratista',
                nombre_firmante=resp_nombre,
                email_firmante=resp_email,
                firma_imagen=resp_firma,
                orden=1,
            )
        else:
            # No tercerizado: coordinador firma por ambos campos → auto_firma_con
            firma_resp = FirmaAPC.objects.create(
                solicitud=solicitud,
                tipo_firma='resp_contratista',
                nombre_firmante=coord_nombre,
                email_firmante='',  # no se envía correo separado
                orden=1,
                auto_firma_con=firma_coord,
            )

        # Firmante 3: coordinador talento humano (orden=2)
        fijo_th = FirmantesFijos.objects.filter(rol='coord_talento_humano', activo=True).first()
        FirmaAPC.objects.create(
            solicitud=solicitud,
            tipo_firma='coord_talento_humano',
            nombre_firmante=fijo_th.nombre if fijo_th else 'Coordinador Talento Humano',
            email_firmante=fijo_th.email if fijo_th else '',
            orden=2,
        )

        # Firmante 4: coordinador gestión de información (orden=3)
        fijo_gi = FirmantesFijos.objects.filter(rol='coord_gestion_info', activo=True).first()
        FirmaAPC.objects.create(
            solicitud=solicitud,
            tipo_firma='coord_gestion_info',
            nombre_firmante=fijo_gi.nombre if fijo_gi else 'Coordinador Gestión de Información',
            email_firmante=fijo_gi.email if fijo_gi else '',
            orden=3,
        )

        # Enviar correos del primer turno (orden=1)
        enviar_correos_firma(solicitud_id, orden=1)

        # Si hay carnet solicitado → notificar destinatarios inmediatamente
        _CLAVES_CARNET = {'carnet', 'tarjeta_chip'}
        permisos_set = set(
            solicitud.permisos_solicitados.values_list('permiso_clave', flat=True)
        )
        if permisos_set & _CLAVES_CARNET:
            from ..email_service import enviar_correos_carnet
            enviar_correos_carnet(solicitud_id)

    except Exception as e:
        import traceback
        print(f'[APC CREAR FIRMAS] error solicitud_id={solicitud_id}: {e}')
        traceback.print_exc()
