import threading
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

from ..models import FirmaAPC, SolicitudAPC
from ..auth import decode_token
from . import APCAPIView as APIView


def _get_firma_from_token(token: str):
    """Valida el token de firma y retorna la FirmaAPC o (None, error_msg)."""
    try:
        payload = decode_token(token)
    except ValueError as e:
        return None, str(e)

    if payload.get('tipo') != 'firma_apc':
        return None, 'Token inválido para esta operación'

    firma_id = payload.get('firma_id')
    try:
        firma = FirmaAPC.objects.select_related('solicitud').get(id=firma_id)
    except FirmaAPC.DoesNotExist:
        return None, 'Firma no encontrada'

    if firma.firmado:
        return None, 'Esta firma ya fue registrada'

    return firma, None


class FirmaDetailView(APIView):
    """Retorna los datos del formulario para que el firmante los revise antes de firmar. Público."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        token = request.query_params.get('token', '')
        if not token:
            return Response({'detail': 'Token requerido'}, status=status.HTTP_400_BAD_REQUEST)

        firma, error = _get_firma_from_token(token)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        s = firma.solicitud
        permisos = list(s.permisos_solicitados.values_list('permiso_clave', flat=True))
        firmas_all = list(s.firmas.order_by('orden').values(
            'tipo_firma', 'nombre_firmante', 'firmado', 'fecha_firma'
        ))

        return Response({
            'firma_id': firma.id,
            'tipo_firma': firma.tipo_firma,
            'tipo_firma_label': firma.get_tipo_firma_display(),
            'nombre_firmante': firma.nombre_firmante,
            'solicitud': {
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
                'num_registro_tarjeta': s.num_registro_tarjeta,
                'nombre_empresa_contratista': s.nombre_empresa_contratista,
                'responsable_entrenamiento': s.responsable_entrenamiento,
                'fecha_entrenamiento': str(s.fecha_entrenamiento) if s.fecha_entrenamiento else None,
                'entrenamiento_dgh': s.entrenamiento_dgh,
                'entrenamiento_correo': s.entrenamiento_correo,
                'entrenamiento_aplicativos': s.entrenamiento_aplicativos,
                'entrenamiento_intranet': s.entrenamiento_intranet,
                'firma_funcionario': s.firma_funcionario,
                'permisos': permisos,
            },
            'firmas_estado': firmas_all,
        })


class FirmarView(APIView):
    """Registra la firma de un firmante. Público (autenticado por token)."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        token = request.data.get('token', '')
        firma_imagen = request.data.get('firma_imagen', '').strip()

        if not token:
            return Response({'detail': 'Token requerido'}, status=status.HTTP_400_BAD_REQUEST)
        if not firma_imagen:
            return Response({'detail': 'La firma es obligatoria'}, status=status.HTTP_400_BAD_REQUEST)

        firma, error = _get_firma_from_token(token)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        firma.firmado = True
        firma.firma_imagen = firma_imagen
        firma.fecha_firma = now
        firma.save(update_fields=['firmado', 'firma_imagen', 'fecha_firma'])

        # Auto-firmar las que dependen de esta
        for auto in FirmaAPC.objects.filter(auto_firma_con=firma, firmado=False):
            auto.firmado = True
            auto.firma_imagen = firma_imagen
            auto.fecha_firma = now
            auto.save(update_fields=['firmado', 'firma_imagen', 'fecha_firma'])

        threading.Thread(
            target=_avanzar_flujo,
            args=(firma.solicitud_id, firma.orden),
            daemon=True,
        ).start()

        return Response({'ok': True, 'mensaje': 'Firma registrada correctamente.'})


def _avanzar_flujo(solicitud_id: int, orden_actual: int):
    from django.db import close_old_connections
    from ..email_service import enviar_correos_firma, enviar_correos_completado

    close_old_connections()
    try:
        solicitud = SolicitudAPC.objects.get(id=solicitud_id)

        # Verificar si todas las firmas del orden actual están completas
        pendientes_orden = FirmaAPC.objects.filter(
            solicitud=solicitud,
            orden=orden_actual,
            firmado=False,
        ).count()

        if pendientes_orden > 0:
            return  # todavía hay firmas pendientes en este orden

        # Buscar el siguiente orden con firmas pendientes
        from django.db.models import Min
        siguiente = (
            FirmaAPC.objects
            .filter(solicitud=solicitud, firmado=False, orden__gt=orden_actual)
            .exclude(auto_firma_con__isnull=False)
            .aggregate(sig=Min('orden'))['sig']
        )

        if siguiente is not None:
            enviar_correos_firma(solicitud_id, siguiente)
        else:
            # Todas las firmas completadas
            solicitud.estado = 'COMPLETADO'
            solicitud.save(update_fields=['estado'])
            enviar_correos_completado(solicitud_id)

    except Exception as e:
        import traceback
        print(f'[APC FLUJO] error solicitud_id={solicitud_id}: {e}')
        traceback.print_exc()
