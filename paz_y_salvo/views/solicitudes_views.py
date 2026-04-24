from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import SolicitudPS, SolicitudPSArchivo, EncuestaRetiro
from ..permissions import require_roles

MAX_ARCHIVO_MB = 10
EXTS_PERMITIDAS = {'pdf', 'png', 'jpg', 'jpeg'}


class SolicitudPSCreateView(APIView):
    """Endpoint público — no requiere autenticación."""
    permission_classes = []
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        nombre = request.data.get('nombre', '').strip()
        identificacion = request.data.get('identificacion', '').strip()
        correo = request.data.get('correo', '').strip()

        if not nombre or not identificacion:
            return Response(
                {'detail': 'Nombre e identificación son obligatorios'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not identificacion.isdigit():
            return Response(
                {'detail': 'La identificación debe contener solo números'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        archivos_data = []
        for archivo in request.FILES.getlist('archivos'):
            ext = archivo.name.rsplit('.', 1)[-1].lower() if '.' in archivo.name else ''
            if ext not in EXTS_PERMITIDAS:
                continue
            contenido = archivo.read()
            if len(contenido) > MAX_ARCHIVO_MB * 1024 * 1024:
                return Response(
                    {'detail': f'El archivo {archivo.name} supera {MAX_ARCHIVO_MB} MB'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            mime = archivo.content_type or ('application/pdf' if ext == 'pdf' else f'image/{ext}')
            archivos_data.append({
                'nombre_original': archivo.name,
                'contenido': contenido,
                'tipo_mime': mime,
            })

        if not archivos_data:
            return Response(
                {'detail': 'Adjunta al menos un archivo PDF o imagen válido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sol = SolicitudPS.objects.create(
            nombre=nombre,
            identificacion=identificacion,
            correo=correo or None,
        )
        for a in archivos_data:
            SolicitudPSArchivo.objects.create(
                solicitud=sol,
                nombre_original=a['nombre_original'],
                contenido=a['contenido'],
                tipo_mime=a['tipo_mime'],
            )

        return Response({
            'ok': True,
            'solicitud_id': sol.id,
            'archivos': [a['nombre_original'] for a in archivos_data],
            'mensaje': 'Solicitud recibida correctamente. El área de Talento Humano la procesará pronto.',
        }, status=status.HTTP_201_CREATED)


class SolicitudPSListView(APIView):
    permission_classes = [require_roles('paz_salvo', 'admin')]

    def get(self, request):
        solicitudes = (
            SolicitudPS.objects
            .prefetch_related('archivos')
            .order_by('-fecha_creacion')[:200]
        )
        result = []
        for s in solicitudes:
            result.append({
                'id': s.id,
                'nombre': s.nombre,
                'identificacion': s.identificacion,
                'correo': s.correo,
                'estado': s.estado,
                'fecha_creacion': str(s.fecha_creacion),
                'procesado_por': s.procesado_por,
                'archivos': list(s.archivos.values('id', 'nombre_original', 'tipo_mime')),
            })
        return Response(result)


class SolicitudPSProcesarView(APIView):
    permission_classes = [require_roles('paz_salvo', 'admin')]

    def patch(self, request, sol_id):
        try:
            sol = SolicitudPS.objects.get(id=sol_id)
        except SolicitudPS.DoesNotExist:
            return Response({'detail': 'No encontrada'}, status=status.HTTP_404_NOT_FOUND)
        sol.estado = 'PROCESADA'
        sol.procesado_por = request.pys_user['usunombre']
        sol.save(update_fields=['estado', 'procesado_por'])
        return Response({'ok': True})


class ArchivoSolicitudView(APIView):
    permission_classes = [require_roles('paz_salvo', 'admin')]

    def get(self, request, archivo_id):
        try:
            archivo = SolicitudPSArchivo.objects.get(id=archivo_id)
        except SolicitudPSArchivo.DoesNotExist:
            return Response({'detail': 'Archivo no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        contenido = bytes(archivo.contenido)
        response = HttpResponse(contenido, content_type=archivo.tipo_mime)
        response['Content-Disposition'] = f'inline; filename="{archivo.nombre_original}"'
        return response


class EncuestaRetiroExisteView(APIView):
    permission_classes = [require_roles('paz_salvo', 'admin')]

    def get(self, request, identificacion):
        enc = EncuestaRetiro.objects.filter(identificacion=identificacion).order_by('-id').first()
        if not enc:
            return Response({'existe': False})
        return Response({
            'existe': True,
            'nombre': enc.nombre,
            'fecha_retiro': str(enc.fecha_retiro) if enc.fecha_retiro else None,
            'fecha_creacion': str(enc.fecha_creacion),
        })


class EncuestaRetiroCreateView(APIView):
    """Endpoint público — no requiere autenticación."""
    permission_classes = []
    authentication_classes = []

    CALIFS_KEYS = [
        'compañeros', 'formacion', 'ambiente', 'reconocimiento',
        'carga_trabajo', 'superior', 'beneficios', 'salario',
        'valores', 'cultura', 'trabajo_equipo',
    ]
    CALIFS_VALIDOS = {'excelente', 'buena', 'mala', None, ''}

    def post(self, request):
        data = request.data
        nombre = str(data.get('nombre', '')).strip()
        identificacion = str(data.get('identificacion', '')).strip()
        correo = str(data.get('correo', '')).strip()
        fecha_retiro = data.get('fecha_retiro')

        if not nombre or not identificacion:
            return Response({'detail': 'Nombre e identificación son obligatorios'}, status=status.HTTP_400_BAD_REQUEST)
        if not identificacion.isdigit():
            return Response({'detail': 'La identificación debe contener solo números'}, status=status.HTTP_400_BAD_REQUEST)

        for key in self.CALIFS_KEYS:
            val = data.get(f'calif_{key}') or None
            if val and val not in self.CALIFS_VALIDOS:
                return Response(
                    {'detail': f'Valor inválido para calif_{key}: {val}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        enc = EncuestaRetiro.objects.create(
            nombre=nombre,
            identificacion=identificacion,
            correo=correo,
            fecha_retiro=fecha_retiro,
            aspectos_positivos=data.get('aspectos_positivos'),
            actividades_sugeridas=data.get('actividades_sugeridas'),
            calif_compañeros=data.get('calif_compañeros') or None,
            calif_formacion=data.get('calif_formacion') or None,
            calif_ambiente=data.get('calif_ambiente') or None,
            calif_reconocimiento=data.get('calif_reconocimiento') or None,
            calif_carga_trabajo=data.get('calif_carga_trabajo') or None,
            calif_superior=data.get('calif_superior') or None,
            calif_beneficios=data.get('calif_beneficios') or None,
            calif_salario=data.get('calif_salario') or None,
            calif_valores=data.get('calif_valores') or None,
            calif_cultura=data.get('calif_cultura') or None,
            calif_trabajo_equipo=data.get('calif_trabajo_equipo') or None,
        )
        return Response({'ok': True, 'message': 'Encuesta guardada correctamente'}, status=status.HTTP_201_CREATED)
