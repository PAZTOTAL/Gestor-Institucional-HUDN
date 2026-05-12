from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import pandas as pd
import numpy as np
import io
import os
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from core.mixins import AccessControlMixin
from django.conf import settings
from .models import RegistroDescargaCertificado, SolicitudCertificadoEmail, DatosCertificadoDIAN
from django.db import connections
from django.contrib.auth.models import User
from django.contrib.auth import login
from usuarios.models import PerfilUsuario, PermisoApp
from django.core.mail import EmailMessage
import json

def find_institutional_email(username):
    """
    Busca el correo electrónico en la tabla GENUSUARIO de Dinámica.
    """
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute("SELECT USUEMAIL FROM GENUSUARIO WHERE UPPER(USUNOMBRE) = UPPER(%s)", [username])
            row = cursor.fetchone()
            if row and row[0]:
                return row[0].strip()
    except Exception as e:
        print(f"Error buscando email de {username}: {e}")
    return None

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

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

        # 1. ¿Ya está registrado en el Gestor Institucional?
        from usuarios.models import PerfilUsuario
        perfil_existente = PerfilUsuario.objects.filter(cedula=identificador).first()
        if perfil_existente:
            return self.render_to_response({
                'info_msg': 'Usted ya cuenta con un registro en el Gestor Institucional.',
                'action_url': '/login/',
                'action_label': 'INICIAR SESIÓN'
            })

        es_funcionario = False
        
        # 2. ¿Existe en Dinámica (GENUSUARIO)?
        try:
            with connections['readonly'].cursor() as cursor:
                cursor.execute("SELECT 1 FROM GENUSUARIO WHERE UPPER(USUNOMBRE) = UPPER(%s) OR NumeroDocumento = %s", [identificador, identificador])
                es_funcionario = cursor.fetchone() is not None
        except Exception as e:
            print("Error conectado a Dinámica en LoginRápido:", e)

        # 3. ¿Existe en los listados del Formulario 220 (Cargados en local)?
        if not es_funcionario:
            es_funcionario = DatosCertificadoDIAN.objects.filter(cedula=identificador).exists()

        if es_funcionario:
            # Es funcionario pero no se ha registrado
            return self.render_to_response({
                'info_msg': 'Usted es funcionario activo del HUDN, pero aún no se ha registrado en esta aplicación.',
                'action_url': '/registro/',
                'action_label': 'REGISTRARME AHORA',
                'alert_type': 'warning'
            })
        else:
            # No aparece en ningún listado oficial
            return self.render_to_response({
                'error_msg': 'El identificador ingresado no se encuentra en los listados oficiales de Planta o Formulario 220 del HUDN. Si cree que es un error, contacte a Contabilidad.'
            })

def save_pdf_to_server(cedula, anio, request_user, request_ip):
    """
    Función auxiliar para generar y guardar el PDF en el servidor.
    """
    try:
        data = DatosCertificadoDIAN.objects.get(cedula=cedula, anio_gravable=anio)
    except DatosCertificadoDIAN.DoesNotExist:
        return None, f"Cédula {cedula} no encontrada en la base de datos de {anio}."

    template_path = settings.DIAN_TEMPLATE_PATH
    output_dir = settings.DIAN_OUTPUT_DIR

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(template_path):
        return None, f"Error: No se encuentra la plantilla PDF en {template_path}."

    try:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 9)
        
        can.drawString(320, 737, str(anio)) # Año Gravable
        can.drawString(135, 689, "891200210") # NIT HUDN
        can.drawString(194, 689, "8")         # DV
        can.drawString(102, 674, "HOSPITAL UNIVERSITARIO DEPARTAMENTAL DE NARIÑO ESE")
        can.drawString(210, 292, "HOSPITAL UNIVERSITARIO DEPARTAMENTAL DE NARIÑO E.S.E")
        
        can.drawString(55, 653, "13") 
        can.drawString(160, 653, cedula)
        can.drawString(235, 653, data.primer_apellido.upper())
        can.drawString(330, 653, data.segundo_apellido.upper())
        can.drawString(425, 653, data.primer_nombre.upper())
        can.drawString(520, 653, data.otros_nombres.upper())

        can.drawString(62, 626, str(anio))
        can.drawString(98, 626, "01")
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
            
            output_filename = f"Certificado_220_{cedula}_{anio}.pdf"
            output_filepath = os.path.join(output_dir, output_filename)
            with open(output_filepath, "wb") as f_out:
                output.write(f_out)
            
            RegistroDescargaCertificado.objects.create(
                usuario=request_user,
                cedula_consultada=cedula,
                ip_descarga=request_ip
            )
            
            return output_filepath, None

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return None, f"Error Técnico en la generación del PDF: {str(e)}"

def solicitar_certificado_email(request):
    """
    Registra una solicitud para envío por Correo Institucional y envía el PDF.
    """
    if not request.user.is_authenticated:
        return HttpResponse("No autorizado", status=401)
    
    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return HttpResponse("Falta Cédula", status=400)

    # 1. Buscar email institucional
    email_destino = find_institutional_email(request.user.username)
    
    if not email_destino:
        # Fallback: intentar buscar por la cédula si el username no coincide
        email_destino = find_institutional_email(cedula)
    
    if not email_destino:
        return HttpResponse("No se encontró un correo institucional registrado para este usuario. Por favor contacte a Sistemas.", status=404)

    nombre_emp = "Funcionario"
    try:
        dato = DatosCertificadoDIAN.objects.filter(cedula=cedula).first()
        if dato:
            nombre_emp = f"{dato.primer_nombre} {dato.primer_apellido}"
    except:
        pass

    try:
        # 2. Generar y guardar el PDF
        filepath, error = save_pdf_to_server(cedula, 2025, request.user, get_client_ip(request))
        
        if error:
            return HttpResponse(f"Error generando PDF: {error}", status=500)

        # 3. Enviar Correo
        try:
            subject = f"Certificado de Ingresos y Retenciones 2025 - {nombre_emp}"
            body = f"""
            Cordial saludo, Sr(a). {nombre_emp}.
            
            Adjunto encontrará su Certificado de Ingresos y Retenciones para el año gravable 2025, 
            generado a través del Gestor Institucional HUDN.
            
            Este es un correo automático, por favor no responda a este mensaje.
            
            Atentamente,
            Oficina de Contabilidad
            Hospital Universitario Departamental de Nariño E.S.E
            """
            
            email = EmailMessage(
                subject,
                body,
                settings.EMAIL_HOST_USER,
                [email_destino],
            )
            
            # Adjuntar el archivo
            email.attach_file(filepath)
            email.send()
            
            # 4. Registrar en DB
            SolicitudCertificadoEmail.objects.create(
                usuario=request.user,
                cedula_consultada=cedula,
                nombre_empleado=nombre_emp,
                email_envio=email_destino,
                procesado=True
            )
        except Exception as e:
            return HttpResponse(f"Error enviando el correo: {str(e)}", status=500)

        # Retornar Vista de Éxito Premium
        msg = f"""
        <html>
        <head>
            <title>Certificado Enviado</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-slate-50 flex items-center justify-center h-screen font-sans border-t-8 border-blue-600">
            <div class="bg-white p-12 rounded-[2.5rem] border border-slate-200 shadow-2xl max-w-lg w-full text-center">
                <div class="w-20 h-20 bg-blue-600 text-white rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-xl">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
                </div>
                
                <h1 class="text-3xl font-black text-slate-800 uppercase tracking-tighter mb-4">¡Certificado Enviado!</h1>
                <p class="text-slate-500 text-lg font-medium leading-relaxed mb-8">
                    Sr(a). {nombre_emp}, su certificado ha sido enviado exitosamente a:<br>
                    <span class="text-blue-600 font-black underline">{email_destino}</span>
                </p>

                <p class="text-[11px] font-black text-slate-400 uppercase tracking-widest animate-pulse mb-6">
                    Cerrando sesión segura...
                </p>

                <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-10">
                    <div class="bg-blue-600 h-full w-full origin-left animate-[progress_5s_linear_forwards]"></div>
                </div>
                
                <button onclick="cerrarVentana()" class="w-full py-5 bg-slate-900 text-white rounded-2xl font-black uppercase text-sm tracking-[0.2em] shadow-xl hover:bg-slate-800 active:scale-95 transition-all">
                    Finalizar
                </button>
            </div>

            <script>
                function cerrarVentana() {{
                    window.close();
                    setTimeout(() => {{ window.location.href = '/'; }}, 500);
                }}
                setTimeout(cerrarVentana, 5000);
            </script>
            <style>
                @keyframes progress {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
            </style>
        </body>
        </html>
        """
        return HttpResponse(msg)

    except Exception as e:
        return HttpResponse(f"Error Técnico: {str(e)}", status=500)

class ListarSolicitudesEmailView(AccessControlMixin, ListView):
    model = SolicitudCertificadoEmail
    template_name = 'CertificadosDIAN/lista_solicitudes.html'
    context_object_name = 'solicitudes'
    permission_type = 'view'

    def get_queryset(self):
        return SolicitudCertificadoEmail.objects.all().order_by('-fecha_solicitud')

def marcar_procesado_email(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse("No autorizado", status=401)
    
    solicitud = get_object_or_404(SolicitudCertificadoEmail, pk=pk)
    solicitud.procesado = True
    solicitud.save()
    return redirect('certificados_dian:lista_solicitudes')

class CertificadosDashboardView(AccessControlMixin, TemplateView):
    permission_type = 'view'
    template_name = 'CertificadosDIAN/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Certificado de Ingresos Generación de Certificados y Bienes 2025"
        
        ultima_descarga = RegistroDescargaCertificado.objects.filter(
            usuario=self.request.user
        ).order_by('-fecha_descarga').first()
        
        if ultima_descarga:
            context['cedula_previa'] = ultima_descarga.cedula_consultada
        else:
            context['cedula_previa'] = ''
            
        return context

def generar_certificado_ingresos(request):
    """
    Genera el Formulario 220 (DIAN) y lo descarga directamente en el navegador.
    """
    if not request.user.is_authenticated:
        return HttpResponse("No autorizado", status=401)

    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return HttpResponse("Debe proporcionar un número de cédula.", status=400)
    
    anio = int(request.GET.get('anio', 2025))
    
    filepath, error = save_pdf_to_server(cedula, anio, request.user, get_client_ip(request))
    
    if error:
        return HttpResponse(error, status=404 if "no encontrada" in error else 500)

    # Servir el archivo para descarga inmediata
    with open(filepath, 'rb') as f:
        pdf_data = f.read()
        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = os.path.basename(filepath)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
