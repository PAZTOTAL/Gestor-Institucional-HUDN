import threading
from django.utils import timezone
from django.db.models import Prefetch
from rest_framework.response import Response
from rest_framework import status

from ..models import PazSalvo, Validacion, Area
from ..permissions import IsAuthenticated, require_roles
from . import PysAPIView as APIView


def _ps_to_dict(ps: PazSalvo, include_validaciones=True) -> dict:
    d = {
        'id': ps.id,
        'identificacion': ps.identificacion,
        'nombre': ps.nombre,
        'cargo': ps.cargo,
        'dependencia': ps.dependencia,
        'coordinador': ps.coordinador,
        'fecha_retiro': str(ps.fecha_retiro),
        'estado': ps.estado,
        'archivado': ps.archivado,
        'creado_por': ps.creado_por,
        'correo': ps.correo,
        'fecha_creacion': str(ps.fecha_creacion),
    }
    if include_validaciones:
        # Si vienen prefetched (lista), usa el caché; si no (detalle), hace la query
        if hasattr(ps, '_prefetched_objects_cache') and 'validaciones' in ps._prefetched_objects_cache:
            vals = ps.validaciones.all()
        else:
            vals = (
                Validacion.objects
                .filter(ps=ps)
                .select_related('area')
                .order_by('area__orden', 'area__id')
            )
        d['validaciones'] = [
            {
                'id': v.id,
                'area_id': v.area_id,
                'area_nombre': v.area.nombre,
                'responsable': v.area.responsable,
                'orden': v.area.orden,
                'estado': v.estado,
                'observacion': v.observacion,
                'fecha': str(v.fecha) if v.fecha else None,
            }
            for v in vals
        ]
    return d


_VALIDACIONES_PREFETCH = Prefetch(
    'validaciones',
    queryset=Validacion.objects.select_related('area').order_by('area__orden', 'area__id'),
)


class PazSalvoListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        archivado = request.query_params.get('archivado', 'false').lower() == 'true'
        qs = PazSalvo.objects.filter(archivado=archivado).prefetch_related(_VALIDACIONES_PREFETCH)
        return Response([_ps_to_dict(ps) for ps in qs])

    def post(self, request):
        # Requiere rol paz_salvo o admin
        user = request.pys_user
        if user.get('rol') not in ('paz_salvo', 'admin'):
            return Response(
                {'detail': 'Se requiere rol paz_salvo o admin'},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data
        required = ['identificacion', 'nombre', 'cargo', 'dependencia', 'coordinador', 'fechaRetiro']
        for field in required:
            if not data.get(field):
                return Response(
                    {'detail': f'Campo requerido: {field}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        ps = PazSalvo.objects.create(
            identificacion=data['identificacion'],
            nombre=data['nombre'],
            cargo=data['cargo'],
            dependencia=data['dependencia'],
            coordinador=data['coordinador'],
            fecha_retiro=data['fechaRetiro'],
            creado_por=user['usunombre'],
            correo=data.get('correo'),
        )

        # Crear validaciones para todas las áreas activas
        areas = Area.objects.filter(activa=True)
        for area in areas:
            Validacion.objects.create(ps=ps, area=area)

        # Enviar correos del primer turno en hilo secundario
        from ..email_service import enviar_correos_turno
        threading.Thread(target=enviar_correos_turno, args=(ps.id,), daemon=True).start()

        return Response(_ps_to_dict(ps), status=status.HTTP_201_CREATED)


class PazSalvoEstadisticasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Count
        data = (
            PazSalvo.objects
            .filter(archivado=False)
            .values('estado')
            .annotate(total=Count('id'))
        )
        return Response({row['estado']: row['total'] for row in data})


class PazSalvoDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ps_id):
        try:
            ps = PazSalvo.objects.get(id=ps_id)
        except PazSalvo.DoesNotExist:
            return Response({'detail': 'Paz y Salvo no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(_ps_to_dict(ps))


class PazSalvoArchivarView(APIView):
    permission_classes = [require_roles('paz_salvo', 'admin')]

    def patch(self, request, ps_id):
        try:
            ps = PazSalvo.objects.get(id=ps_id)
        except PazSalvo.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)
        ps.archivado = True
        ps.save(update_fields=['archivado'])
        return Response({'ok': True})


class PazSalvoEstadoView(APIView):
    permission_classes = [require_roles('paz_salvo', 'admin')]

    def patch(self, request, ps_id):
        try:
            ps = PazSalvo.objects.get(id=ps_id)
        except PazSalvo.DoesNotExist:
            return Response({'detail': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)

        nuevo_estado = request.data.get('estado')
        estados_validos = [c[0] for c in PazSalvo.ESTADO_CHOICES]
        if nuevo_estado not in estados_validos:
            return Response(
                {'detail': f'Estado inválido. Válidos: {", ".join(estados_validos)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ps.estado = nuevo_estado
        ps.save(update_fields=['estado'])
        return Response({'ok': True})
