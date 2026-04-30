import threading
from django.utils import timezone
from django.db.models import Min, OuterRef, Subquery, F
from rest_framework.response import Response
from rest_framework import status

from ..models import PazSalvo, Validacion, Area
from ..permissions import IsAuthenticated, require_roles
from ..auth import decode_token
from . import PysAPIView as APIView


class ValidarView(APIView):
    permission_classes = [require_roles('validador', 'admin')]

    def post(self, request, ps_id):
        user = request.pys_user
        area_id = user.get('area_id')
        if not area_id:
            return Response(
                {'detail': 'Este usuario no tiene área de validación asignada'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            val = Validacion.objects.select_related('area').get(ps_id=ps_id, area_id=area_id)
        except Validacion.DoesNotExist:
            return Response(
                {'detail': 'Validación no encontrada para esta área'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if val.estado == 'VALIDADO':
            return Response(
                {'detail': 'Ya validaste este Paz y Salvo'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar turno: el orden mínimo pendiente debe coincidir con esta área
        min_orden = (
            Validacion.objects
            .filter(ps_id=ps_id, estado='PENDIENTE')
            .aggregate(min_orden=Min('area__orden'))['min_orden']
        )
        if min_orden != val.area.orden:
            return Response(
                {'detail': 'Aún no es el turno de tu área'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        val.estado = 'VALIDADO'
        val.fecha = timezone.now()
        val.observacion = request.data.get('observacion')
        val.save()

        # ¿Quedan pendientes en el mismo orden?
        quedan = (
            Validacion.objects
            .filter(ps_id=ps_id, estado='PENDIENTE', area__orden=val.area.orden)
            .count()
        )

        if quedan == 0:
            next_orden = (
                Validacion.objects
                .filter(ps_id=ps_id, estado='PENDIENTE')
                .aggregate(min_orden=Min('area__orden'))['min_orden']
            )
            if next_orden is not None:
                from ..email_service import enviar_correos_turno
                threading.Thread(target=enviar_correos_turno, args=(ps_id,), daemon=True).start()
            else:
                PazSalvo.objects.filter(id=ps_id).update(estado='VALIDADO')

        return Response({'ok': True, 'mensaje': 'Validación registrada correctamente'})


class RechazarView(APIView):
    permission_classes = [require_roles('validador', 'admin')]

    def post(self, request, ps_id):
        user = request.pys_user
        area_id = user.get('area_id')
        if not area_id:
            return Response({'detail': 'Sin área asignada'}, status=status.HTTP_403_FORBIDDEN)

        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'Debe indicar el motivo del rechazo'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            val = Validacion.objects.select_related('area').get(ps_id=ps_id, area_id=area_id)
        except Validacion.DoesNotExist:
            return Response({'detail': 'Validación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        if val.estado in ('VALIDADO', 'RECHAZADO'):
            return Response(
                {'detail': f'Esta validación ya fue procesada: {val.estado}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        min_orden = (
            Validacion.objects
            .filter(ps_id=ps_id, estado='PENDIENTE')
            .aggregate(min_orden=Min('area__orden'))['min_orden']
        )
        if min_orden != val.area.orden:
            return Response({'detail': 'Aún no es el turno de tu área'}, status=status.HTTP_400_BAD_REQUEST)

        val.estado = 'RECHAZADO'
        val.fecha = timezone.now()
        val.observacion = motivo
        val.save()

        ps = PazSalvo.objects.get(id=ps_id)
        ps.estado = 'RECHAZADO'
        ps.save(update_fields=['estado'])

        # Notificar al funcionario si tiene correo
        correo_funcionario = ps.correo
        if not correo_funcionario:
            from ..models import SolicitudPS
            sol = SolicitudPS.objects.filter(
                identificacion=ps.identificacion,
                correo__isnull=False,
            ).exclude(correo='').order_by('-fecha_creacion').first()
            if sol:
                correo_funcionario = sol.correo

        if correo_funcionario:
            threading.Thread(
                target=_notificar_rechazo_funcionario,
                args=(correo_funcionario, ps.nombre, val.area.nombre, val.area.responsable, motivo),
                daemon=True,
            ).start()

        return Response({'ok': True, 'mensaje': 'Paz y Salvo rechazado'})


class RevalidarView(APIView):
    permission_classes = [require_roles('validador', 'admin')]

    def post(self, request, ps_id):
        user = request.pys_user
        area_id = user.get('area_id')
        if not area_id:
            return Response({'detail': 'Sin área asignada'}, status=status.HTTP_403_FORBIDDEN)

        try:
            val = Validacion.objects.select_related('area').get(ps_id=ps_id, area_id=area_id)
        except Validacion.DoesNotExist:
            return Response({'detail': 'Validación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        if val.estado != 'RECHAZADO':
            return Response({'detail': 'Esta validación no está en estado RECHAZADO'}, status=status.HTTP_400_BAD_REQUEST)

        val.estado = 'VALIDADO'
        val.fecha = timezone.now()
        val.observacion = None
        val.save()

        PazSalvo.objects.filter(id=ps_id, estado='RECHAZADO').update(estado='EN_TRAMITE')

        quedan = (
            Validacion.objects
            .filter(ps_id=ps_id, estado='PENDIENTE', area__orden=val.area.orden)
            .count()
        )
        if quedan == 0:
            next_orden = (
                Validacion.objects
                .filter(ps_id=ps_id, estado='PENDIENTE')
                .aggregate(min_orden=Min('area__orden'))['min_orden']
            )
            if next_orden is not None:
                from ..email_service import enviar_correos_turno
                threading.Thread(target=enviar_correos_turno, args=(ps_id,), daemon=True).start()
            else:
                PazSalvo.objects.filter(id=ps_id).update(estado='VALIDADO')

        return Response({'ok': True, 'mensaje': 'Validación cambiada a VALIDADO'})


class MisPendientesView(APIView):
    permission_classes = [require_roles('validador', 'admin')]

    def get(self, request):
        user = request.pys_user
        area_id = user.get('area_id')
        if not area_id:
            return Response([])

        # Subquery: orden mínimo pendiente para cada PS
        min_pending_orden = (
            Validacion.objects
            .filter(ps_id=OuterRef('ps_id'), estado='PENDIENTE')
            .values('ps_id')
            .annotate(m=Min('area__orden'))
            .values('m')
        )

        # Solo mostrar si es el turno del área (min orden pendiente == orden de esta área)
        vals = (
            Validacion.objects
            .filter(area_id=area_id, estado='PENDIENTE', ps__archivado=False)
            .exclude(ps__estado='CANCELADO')
            .annotate(min_orden_ps=Subquery(min_pending_orden))
            .filter(min_orden_ps=F('area__orden'))
            .select_related('ps', 'area')
            .order_by('-ps__fecha_creacion')
        )
        result = []
        for v in vals:
            ps = v.ps
            result.append({
                'id': ps.id,
                'identificacion': ps.identificacion,
                'nombre': ps.nombre,
                'cargo': ps.cargo,
                'dependencia': ps.dependencia,
                'coordinador': ps.coordinador,
                'fecha_retiro': str(ps.fecha_retiro),
                'estado': ps.estado,
                'creado_por': ps.creado_por,
                'fecha_creacion': str(ps.fecha_creacion),
                'mi_estado': v.estado,
                'mi_fecha': str(v.fecha) if v.fecha else None,
                'mi_orden': v.area.orden,
                'mi_observacion': v.observacion,
            })
        return Response(result)


class MisValidacionesView(APIView):
    """Devuelve todas las validaciones del área (pendientes + validadas + rechazadas)."""
    permission_classes = [require_roles('validador', 'admin')]

    def get(self, request):
        user = request.pys_user
        area_id = user.get('area_id')
        if not area_id:
            return Response([])

        # Subquery: orden mínimo pendiente para cada PS (para saber si es el turno)
        min_pending_orden = (
            Validacion.objects
            .filter(ps_id=OuterRef('ps_id'), estado='PENDIENTE')
            .values('ps_id')
            .annotate(m=Min('area__orden'))
            .values('m')
        )

        vals = (
            Validacion.objects
            .filter(area_id=area_id, ps__archivado=False)
            .exclude(ps__estado='CANCELADO')
            .annotate(min_orden_ps=Subquery(min_pending_orden))
            .select_related('ps', 'area')
            .order_by('-ps__fecha_creacion')
        )
        result = []
        for v in vals:
            ps = v.ps
            # es_turno: solo aplica a PENDIENTE; verdadero cuando el orden mínimo
            # pendiente del PS coincide con el orden del área de este validador
            es_turno = (
                v.estado == 'PENDIENTE'
                and v.min_orden_ps is not None
                and v.min_orden_ps == v.area.orden
            )
            result.append({
                'id': ps.id,
                'identificacion': ps.identificacion,
                'nombre': ps.nombre,
                'cargo': ps.cargo,
                'dependencia': ps.dependencia,
                'coordinador': ps.coordinador,
                'fecha_retiro': str(ps.fecha_retiro),
                'estado': ps.estado,
                'creado_por': ps.creado_por,
                'fecha_creacion': str(ps.fecha_creacion),
                'mi_estado': v.estado,
                'mi_fecha': str(v.fecha) if v.fecha else None,
                'mi_orden': v.area.orden,
                'mi_observacion': v.observacion,
                'es_turno': es_turno,
            })
        return Response(result)


class ValidarPorTokenView(APIView):
    permission_classes = []  # acceso público con token propio

    def _decode_validacion_token(self, token):
        try:
            payload = decode_token(token)
        except ValueError as e:
            return None, str(e)
        if payload.get('tipo') != 'validacion':
            return None, 'Token no válido para validación'
        return payload, None

    def get(self, request):
        token = request.query_params.get('token', '')
        payload, err = self._decode_validacion_token(token)
        if err:
            return Response({'detail': err}, status=status.HTTP_401_UNAUTHORIZED)

        ps_id = payload['ps_id']
        area_id = payload['area_id']

        try:
            ps = PazSalvo.objects.get(id=ps_id)
        except PazSalvo.DoesNotExist:
            return Response({'detail': 'PS no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Estado de la validación de esta área
        try:
            mi_val = Validacion.objects.select_related('area').get(ps_id=ps_id, area_id=area_id)
            mi_estado = mi_val.estado
        except Validacion.DoesNotExist:
            mi_estado = None

        vals = (
            Validacion.objects
            .filter(ps=ps)
            .select_related('area')
            .order_by('area__orden', 'area__id')
        )
        ps_data = {
            'id': ps.id,
            'identificacion': ps.identificacion,
            'nombre': ps.nombre,
            'cargo': ps.cargo,
            'dependencia': ps.dependencia,
            'coordinador': ps.coordinador,
            'fecha_retiro': str(ps.fecha_retiro),
            'estado': ps.estado,
            'fecha_creacion': str(ps.fecha_creacion),
            'validaciones': [
                {
                    'id': v.id,
                    'area_id': v.area_id,
                    'area_nombre': v.area.nombre,
                    'orden': v.area.orden,
                    'estado': v.estado,
                    'fecha': str(v.fecha) if v.fecha else None,
                }
                for v in vals
            ],
        }
        return Response({'ps': ps_data, 'area_id': area_id, 'mi_estado': mi_estado, 'token_ok': True})

    def post(self, request):
        token = request.data.get('token', '')
        accion = request.data.get('accion', '')

        payload, err = self._decode_validacion_token(token)
        if err:
            return Response({'detail': err}, status=status.HTTP_401_UNAUTHORIZED)

        ps_id = payload['ps_id']
        area_id = payload['area_id']

        try:
            val = Validacion.objects.select_related('area').get(ps_id=ps_id, area_id=area_id)
        except Validacion.DoesNotExist:
            return Response({'detail': 'Validación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        if val.estado in ('VALIDADO', 'RECHAZADO'):
            return Response(
                {'detail': f'Esta validación ya fue procesada: {val.estado}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        min_orden = (
            Validacion.objects
            .filter(ps_id=ps_id, estado='PENDIENTE')
            .aggregate(min_orden=Min('area__orden'))['min_orden']
        )
        if min_orden != val.area.orden:
            return Response({'detail': 'Aún no es el turno de tu área'}, status=status.HTTP_400_BAD_REQUEST)

        if accion == 'aprobar':
            val.estado = 'VALIDADO'
            val.fecha = timezone.now()
            val.save(update_fields=['estado', 'fecha'])

            quedan = (
                Validacion.objects
                .filter(ps_id=ps_id, estado='PENDIENTE', area__orden=val.area.orden)
                .count()
            )
            if quedan == 0:
                next_orden = (
                    Validacion.objects
                    .filter(ps_id=ps_id, estado='PENDIENTE')
                    .aggregate(min_orden=Min('area__orden'))['min_orden']
                )
                if next_orden is not None:
                    from ..email_service import enviar_correos_turno
                    threading.Thread(target=enviar_correos_turno, args=(ps_id,), daemon=True).start()
                else:
                    PazSalvo.objects.filter(id=ps_id).update(estado='VALIDADO')

            return Response({'ok': True, 'mensaje': 'Validación aprobada correctamente'})

        elif accion == 'rechazar':
            motivo = request.data.get('motivo', '').strip()
            if not motivo:
                return Response(
                    {'detail': 'Debe indicar el motivo del rechazo'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            val.estado = 'RECHAZADO'
            val.fecha = timezone.now()
            val.observacion = motivo
            val.save(update_fields=['estado', 'fecha', 'observacion'])

            PazSalvo.objects.filter(id=ps_id).update(estado='RECHAZADO')

            try:
                ps = PazSalvo.objects.get(id=ps_id)
                correo_funcionario = ps.correo
                if not correo_funcionario:
                    from ..models import SolicitudPS
                    sol = SolicitudPS.objects.filter(
                        identificacion=ps.identificacion,
                        correo__isnull=False,
                    ).exclude(correo='').order_by('-fecha_creacion').first()
                    if sol:
                        correo_funcionario = sol.correo
                if correo_funcionario:
                    threading.Thread(
                        target=_notificar_rechazo_funcionario,
                        args=(correo_funcionario, ps.nombre, val.area.nombre, val.area.responsable, motivo),
                        daemon=True,
                    ).start()
            except Exception:
                pass

            return Response({'ok': True, 'mensaje': 'Paz y Salvo rechazado'})

        return Response({'detail': 'Acción no válida. Use "aprobar" o "rechazar"'}, status=status.HTTP_400_BAD_REQUEST)


def _notificar_rechazo_funcionario(correo: str, nombre: str, area: str, responsable: str, motivo: str):
    from ..email_service import _send_sync, _log
    asunto = 'Tu Paz y Salvo fue rechazado — HUDN'
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
        style="background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:#dc2626;padding:28px 32px;text-align:center;">
            <p style="margin:0;color:#ffffff;font-size:11px;letter-spacing:1.5px;text-transform:uppercase;font-weight:700;">
              Hospital Universitario Departamental de Nariño E.S.E.
            </p>
            <h1 style="margin:10px 0 0;color:#ffffff;font-size:22px;font-weight:800;">✕ Paz y Salvo Rechazado</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <p style="font-size:15px;color:#1e293b;font-weight:700;margin:0 0 8px;">Estimado/a {nombre},</p>
            <p style="font-size:14px;color:#475569;line-height:1.7;margin:0 0 24px;">
              Su trámite de <strong>Paz y Salvo</strong> fue
              <strong style="color:#dc2626;">rechazado</strong> por el área de <strong>{area}</strong>.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
              <tr>
                <td style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:18px 20px;">
                  <p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#991b1b;text-transform:uppercase;">Motivo del rechazo</p>
                  <p style="margin:0;font-size:14px;color:#7f1d1d;line-height:1.6;">{motivo}</p>
                </td>
              </tr>
            </table>
            <p style="font-size:13px;color:#64748b;line-height:1.7;margin:24px 0 0;">
              Comuníquese con <strong>{responsable}</strong> del área de <strong>{area}</strong> para resolver la situación.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f8fafc;padding:18px 32px;border-top:1px solid #e2e8f0;text-align:center;">
            <p style="margin:0;font-size:11px;color:#94a3b8;">Mensaje automático del sistema de Paz y Salvos — HUDN.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
    try:
        _send_sync(correo, asunto, html)
        _log(None, None, correo, asunto, 'ENVIADO')
    except Exception as e:
        _log(None, None, correo, asunto, 'ERROR', str(e))
