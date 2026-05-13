from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import io
import os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from core.mixins import AccessControlMixin
from django.conf import settings
from .models import RegistroDescargaCertificado, DatosCertificadoDIAN, SolicitudCertificadoEmail
from django.db import connections
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario, PermisoApp


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class LoginRapidoView(TemplateView):
    template_name = 'CertificadosDIAN/login_rapido.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('certificados_dian:dashboard')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        identificador = request.POST.get('identificador', '').strip()
        if not identificador:
            return self.render_to_response({'error_msg': 'Debe ingresar un usuario o cédula.'})

        perfil_existente = PerfilUsuario.objects.filter(cedula=identificador).first()
        if perfil_existente:
            return self.render_to_response({
                'info_msg': 'Usted ya cuenta con un registro en el Gestor Institucional.',
                'action_url': '/login/',
                'action_label': 'INICIAR SESIÓN'
            })

        es_funcionario = False
        try:
            with connections['readonly'].cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM GENUSUARIO WHERE UPPER(USUNOMBRE) = UPPER(%s) OR NumeroDocumento = %s",
                    [identificador, identificador]
                )
                es_funcionario = cursor.fetchone() is not None
        except Exception as e:
            print("Error conectado a Dinámica en LoginRápido:", e)

        if not es_funcionario:
            es_funcionario = DatosCertificadoDIAN.objects.filter(cedula=identificador).exists()

        if es_funcionario:
            return self.render_to_response({
                'info_msg': 'Usted es funcionario activo del HUDN, pero aún no se ha registrado en esta aplicación.',
                'action_url': '/registro/',
                'action_label': 'REGISTRARME AHORA',
                'alert_type': 'warning'
            })
        else:
            return self.render_to_response({
                'error_msg': 'El identificador ingresado no se encuentra en los listados oficiales del HUDN. Si cree que es un error, contacte a Contabilidad.'
            })


def _generar_pdf_bytes(cedula, anio):
    """Genera el PDF en memoria y retorna (bytes, nombre_empleado, error)."""
    try:
        data = DatosCertificadoDIAN.objects.get(cedula=cedula, anio_gravable=anio)
    except DatosCertificadoDIAN.DoesNotExist:
        return None, None, f"Cédula {cedula} no encontrada para el año {anio}."

    template_path = settings.DIAN_TEMPLATE_PATH
    if not os.path.exists(template_path):
        return None, None, f"Plantilla PDF no encontrada en {template_path}."

    try:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 9)

        can.drawString(320, 737, str(anio))
        can.drawString(135, 689, "891200210")
        can.drawString(194, 689, "8")
        can.drawString(102, 674, "HOSPITAL UNIVERSITARIO DEPARTAMENTAL DE NARIÑO ESE")
        can.drawString(210, 292, "HOSPITAL UNIVERSITARIO DEPARTAMENTAL DE NARIÑO E.S.E")

        can.drawString(55,  653, "13")
        can.drawString(160, 653, cedula)
        can.drawString(235, 653, data.primer_apellido.upper())
        can.drawString(330, 653, data.segundo_apellido.upper())
        can.drawString(425, 653, data.primer_nombre.upper())
        can.drawString(520, 653, data.otros_nombres.upper())

        can.drawString(62,  626, str(anio))
        can.drawString(98,  626, "01")
        can.drawString(120, 626, "01")
        can.drawString(172, 626, str(anio))
        can.drawString(208, 626, "12")
        can.drawString(230, 626, "31")
        can.drawString(263, 626, str(anio + 1))
        can.drawString(298, 626, "03")
        can.drawString(320, 626, "30")
        can.drawString(365, 626, "PASTO")
        can.drawString(525, 626, "52")
        can.drawString(555, 626, "001")

        box_mapping = {
            'caja_36': 602.4, 'caja_42': 530.4, 'caja_46': 482.4,
            'caja_47': 470.4, 'caja_49': 446.8, 'caja_52': 410.8,
            'caja_53': 386.3, 'caja_54': 374.8, 'caja_56': 351.6,
            'caja_57': 340.0, 'caja_59': 316.0, 'caja_60': 304.0,
        }
        for field_name, y_coord in box_mapping.items():
            val = getattr(data, field_name)
            if val and val > 0:
                txt = f"{float(val):,.0f}".replace(',', '.')
                can.drawRightString(545, y_coord, txt)

        can.save()
        packet.seek(0)

        new_pdf = PdfReader(packet)
        with open(template_path, "rb") as f_template:
            existing_pdf = PdfReader(f_template)
            output = PdfWriter()
            page = existing_pdf.pages[0]
            page.merge_page(new_pdf.pages[0])
            output.add_page(page)

            out_buffer = io.BytesIO()
            output.write(out_buffer)
            pdf_bytes = out_buffer.getvalue()

        nombre_empleado = f"{data.primer_nombre} {data.primer_apellido}".strip()
        return pdf_bytes, nombre_empleado, None

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return None, None, f"Error técnico generando el PDF: {str(e)}"


class CertificadosDashboardView(AccessControlMixin, TemplateView):
    permission_type = 'view'
    template_name = 'CertificadosDIAN/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Certificado de Ingresos — Formulario 220 · 2025"

        ultima_descarga = RegistroDescargaCertificado.objects.filter(
            usuario=self.request.user
        ).order_by('-fecha_descarga').first()

        context['cedula_previa'] = ultima_descarga.cedula_consultada if ultima_descarga else ''
        return context


def generar_certificado_ingresos(request):
    """Genera el Formulario 220 y lo entrega como descarga directa. Registra la trazabilidad."""
    if not request.user.is_authenticated:
        return HttpResponse("No autorizado", status=401)

    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return HttpResponse("Debe proporcionar un número de cédula.", status=400)

    anio = int(request.GET.get('anio', 2025))

    pdf_bytes, nombre_empleado, error = _generar_pdf_bytes(cedula, anio)

    if error:
        return HttpResponse(error, status=404 if "no encontrada" in error else 500)

    # — Guardar también en disco (historial servidor) —
    try:
        output_dir = settings.DIAN_OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"Certificado_220_{cedula}_{anio}.pdf")
        with open(output_filepath, "wb") as f_out:
            f_out.write(pdf_bytes)
    except Exception:
        pass  # No interrumpir la descarga por fallo de guardado en disco

    # — Registrar trazabilidad —
    RegistroDescargaCertificado.objects.create(
        usuario=request.user,
        cedula_consultada=cedula,
        nombre_empleado=nombre_empleado or '',
        anio_gravable=anio,
        ip_descarga=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Certificado_220_{cedula}_{anio}.pdf"'
    return response


class TrazabilidadDescargasView(AccessControlMixin, ListView):
    """Vista de trazabilidad — solo accesible para administradores."""
    model = RegistroDescargaCertificado
    template_name = 'CertificadosDIAN/trazabilidad.html'
    context_object_name = 'registros'
    permission_type = 'view'
    paginate_by = 50

    def get_queryset(self):
        qs = RegistroDescargaCertificado.objects.select_related('usuario').order_by('-fecha_descarga')
        q = self.request.GET.get('q', '').strip()
        anio = self.request.GET.get('anio', '').strip()
        usuario_id = self.request.GET.get('usuario', '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(cedula_consultada__icontains=q) |
                Q(nombre_empleado__icontains=q) |
                Q(usuario__username__icontains=q) |
                Q(usuario__first_name__icontains=q) |
                Q(usuario__last_name__icontains=q)
            )
        if anio:
            qs = qs.filter(anio_gravable=anio)
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = RegistroDescargaCertificado.objects.count()
        context['usuarios'] = User.objects.filter(
            id__in=RegistroDescargaCertificado.objects.values_list('usuario_id', flat=True).distinct()
        ).order_by('last_name', 'first_name')
        context['q'] = self.request.GET.get('q', '')
        context['anio_filtro'] = self.request.GET.get('anio', '')
        context['usuario_filtro'] = self.request.GET.get('usuario', '')
        return context


def _es_admin(user):
    """Verifica si el usuario es administrador global."""
    if user.is_superuser:
        return True
    try:
        return user.perfil.categoria == 'ADMIN'
    except Exception:
        return False


class ListaSolicitudesView(LoginRequiredMixin, ListView):
    """Lista de todas las descargas realizadas + opción WhatsApp. Solo administradores."""
    model = RegistroDescargaCertificado
    template_name = 'CertificadosDIAN/lista_solicitudes.html'
    context_object_name = 'registros'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not _es_admin(request.user):
            from django.contrib import messages
            messages.error(request, 'Solo los administradores pueden acceder a esta sección.')
            return redirect('certificados_dian:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        from django.db.models import Q
        qs = RegistroDescargaCertificado.objects.select_related('usuario').order_by('-fecha_descarga')
        q = self.request.GET.get('q', '').strip()
        anio = self.request.GET.get('anio', '').strip()
        wp = self.request.GET.get('wp', '').strip()
        if q:
            qs = qs.filter(
                Q(cedula_consultada__icontains=q) |
                Q(nombre_empleado__icontains=q) |
                Q(usuario__username__icontains=q) |
                Q(usuario__first_name__icontains=q) |
                Q(usuario__last_name__icontains=q)
            )
        if anio:
            qs = qs.filter(anio_gravable=anio)
        if wp == 'si':
            qs = qs.filter(enviado_whatsapp=True)
        elif wp == 'no':
            qs = qs.filter(enviado_whatsapp=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total'] = RegistroDescargaCertificado.objects.count()
        context['total_wp'] = RegistroDescargaCertificado.objects.filter(enviado_whatsapp=True).count()
        context['q'] = self.request.GET.get('q', '')
        context['anio_filtro'] = self.request.GET.get('anio', '')
        context['wp_filtro'] = self.request.GET.get('wp', '')
        return context


def registrar_envio_whatsapp(request, pk):
    """Marca un registro como enviado por WhatsApp y guarda el teléfono."""
    if not request.user.is_authenticated or not _es_admin(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    registro = get_object_or_404(RegistroDescargaCertificado, pk=pk)
    try:
        import json as _json
        data = _json.loads(request.body)
        telefono = data.get('telefono', '').strip()
        if not telefono:
            return JsonResponse({'error': 'Número de teléfono requerido'}, status=400)
        registro.enviado_whatsapp = True
        registro.telefono_whatsapp = telefono
        registro.fecha_whatsapp = timezone.now()
        registro.save(update_fields=['enviado_whatsapp', 'telefono_whatsapp', 'fecha_whatsapp'])
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
