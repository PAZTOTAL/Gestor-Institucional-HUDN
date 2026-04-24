from rest_framework.views import APIView
from rest_framework.response import Response

from ..models import LogAcceso, EmailLog
from ..permissions import require_roles


class LogAccesosView(APIView):
    permission_classes = [require_roles('admin')]

    def get(self, request):
        qs = LogAcceso.objects.all()[:200]
        return Response([
            {
                'id': l.id,
                'usunombre': l.usunombre,
                'nombre': l.nombre,
                'rol': l.rol,
                'accion': l.accion,
                'ip': l.ip,
                'fecha_hora': str(l.fecha_hora),
            }
            for l in qs
        ])


class LogCorreosView(APIView):
    permission_classes = [require_roles('admin')]

    def get(self, request):
        qs = EmailLog.objects.all()[:200]
        return Response([
            {
                'id': l.id,
                'ps_id': l.ps_id,
                'area_id': l.area_id,
                'destinatario': l.destinatario,
                'asunto': l.asunto,
                'estado': l.estado,
                'error_msg': l.error_msg,
                'fecha_hora': str(l.fecha_hora),
            }
            for l in qs
        ])


class LogEstadisticasView(APIView):
    permission_classes = [require_roles('admin')]

    def get(self, request):
        from django.db.models import Count
        accesos = LogAcceso.objects.values('accion').annotate(total=Count('id'))
        correos = EmailLog.objects.values('estado').annotate(total=Count('id'))
        return Response({
            'accesos': {row['accion']: row['total'] for row in accesos},
            'correos': {row['estado']: row['total'] for row in correos},
        })
