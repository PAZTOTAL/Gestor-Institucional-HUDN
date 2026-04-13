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
from .models import RegistroDescargaCertificado, SolicitudCertificadoWhatsapp, DatosCertificadoDIAN
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

        es_valido = False
        
        # 1. Validar si existe en Dinámica (GENUSUARIO)
        try:
            with connections['readonly'].cursor() as cursor:
                cursor.execute("SELECT 1 FROM GENUSUARIO WHERE UPPER(USUNOMBRE) = UPPER(%s)", [identificador])
                es_valido = cursor.fetchone() is not None
        except Exception as e:
            print("Error conectado a Dinámica en LoginRápido:", e)

        # 2. Validar si existe en la base de datos local (Ya migrado de Excel)
        if not es_valido:
            es_valido = DatosCertificadoDIAN.objects.filter(cedula=identificador).exists()

        if es_valido:
            # Login exitoso - auto provisionar y logear
            user, created = User.objects.get_or_create(username=identificador)
            if created:
                user.set_unusable_password()
                user.save()
            
            # Asegurar perfil y permisos de CertificadosDIAN por defecto
            PerfilUsuario.objects.get_or_create(user=user, defaults={'categoria': 'LECTOR'})
            PermisoApp.objects.get_or_create(user=user, app_label="CertificadosDIAN", defaults={"permitido": True})

            login(request, user)
            return redirect('certificados_dian:dashboard')
        else:
            return self.render_to_response({'error_msg': 'Identificador no encontrado en Dinámica ni en los listados del Formulario 220.'})

def solicitar_certificado_whatsapp(request):
    """
    Registra una solicitud para envío por WhatsApp y retorna una página de éxito.
    """
    if not request.user.is_authenticated:
        return HttpResponse("No autorizado", status=401)
    
    cedula = request.GET.get('cedula', '').strip()
    telefono = request.GET.get('telefono', '').strip()
    
    if not cedula or not telefono:
        return HttpResponse("Falta Cédula o Teléfono", status=400)

    nombre_emp = "Funcionario"
    try:
        dato = DatosCertificadoDIAN.objects.filter(cedula=cedula).first()
        if dato:
            nombre_emp = f"{dato.primer_nombre} {dato.primer_apellido}"
    except:
        pass

    try:
        SolicitudCertificadoWhatsapp.objects.create(
            usuario=request.user,
            cedula_consultada=cedula,
            nombre_empleado=nombre_emp,
            telefono=telefono
        )
        
        # Retornar Vista de Éxito Premium (Limpia y moderna)
        msg = f"""
        <html>
        <head>
            <title>Solicitud Recibida</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-slate-50 flex items-center justify-center h-screen font-sans border-t-8 border-green-500">
            <div class="bg-white p-12 rounded-[2.5rem] border border-slate-200 shadow-2xl max-w-lg w-full text-center">
                <div class="w-20 h-20 bg-green-600 text-white rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-xl">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
                
                <h1 class="text-3xl font-black text-slate-800 uppercase tracking-tighter mb-4">Solicitud Registrada</h1>
                <p class="text-slate-500 text-lg font-medium leading-relaxed mb-8">
                    Sr(a). {nombre_emp}, su certificado será enviado <br>
                    <span class="text-green-600 font-black">en un lapso máximo de 16 horas.</span>
                </p>

                <p class="text-[11px] font-black text-slate-400 uppercase tracking-widest animate-pulse mb-6">
                    Saliendo de la aplicación...
                </p>

                <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-10">
                    <div class="bg-green-600 h-full w-full origin-left animate-[progress_5s_linear_forwards]"></div>
                </div>
                
                <button onclick="cerrarVentana()" class="w-full py-5 bg-slate-900 text-white rounded-2xl font-black uppercase text-sm tracking-[0.2em] shadow-xl hover:bg-slate-800 active:scale-95 transition-all">
                    Terminar Ahora
                </button>
            </div>

            <script>
                function cerrarVentana() {{
                    // Al ser abierta como popup por el dashboard, este window.close() es permitido.
                    window.close();
                    self.close();
                    // Fallback para navegadores antiguos
                    window.open('', '_self', '').close();
                }}
                setTimeout(cerrarVentana, 3000);
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

class ListarSolicitudesWhatsappView(AccessControlMixin, ListView):
    model = SolicitudCertificadoWhatsapp
    template_name = 'CertificadosDIAN/lista_solicitudes.html'
    context_object_name = 'solicitudes'
    permission_type = 'view'

    def get_queryset(self):
        return SolicitudCertificadoWhatsapp.objects.all().order_by('-fecha_solicitud')

def marcar_procesado_whatsapp(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse("No autorizado", status=401)
    
    solicitud = get_object_or_404(SolicitudCertificadoWhatsapp, pk=pk)
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
    Genera el Formulario 220 (DIAN) inyectando datos de la base de datos en una plantilla PDF.
    """
    if not request.user.is_authenticated:
        return HttpResponse("No autorizado", status=401)

    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return HttpResponse("Debe proporcionar un número de cédula.", status=400)
    
    anio = int(request.GET.get('anio', 2025))
    
    try:
        data = DatosCertificadoDIAN.objects.get(cedula=cedula, anio_gravable=anio)
    except DatosCertificadoDIAN.DoesNotExist:
        return HttpResponse(f"Cédula {cedula} no encontrada en la base de datos de {anio}.", status=404)

    template_path = settings.DIAN_TEMPLATE_PATH
    output_dir = settings.DIAN_OUTPUT_DIR

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(template_path):
        return HttpResponse(f"Error: No se encuentra la plantilla PDF en {template_path}.", status=404)

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
                usuario=request.user,
                cedula_consultada=cedula,
                ip_descarga=get_client_ip(request)
            )

            msg = f"""
            <html>
            <head>
                <title>PDF Generado</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-slate-50 flex items-center justify-center h-screen font-sans border-t-8 border-blue-600">
                <div class="bg-white p-12 rounded-[2.5rem] border border-slate-200 shadow-2xl max-w-lg w-full text-center">
                    <h2 class="text-3xl font-black text-blue-600 uppercase tracking-tighter mb-4">¡PDF GUARDADO!</h2>
                    <p class="text-slate-500 text-lg font-medium leading-relaxed mb-8">
                        El certificado para la cédula <b>{cedula}</b> se ha guardado en el servidor institucional.
                    </p>
                    <button onclick="window.close();" class="w-full py-5 bg-slate-900 text-white rounded-2xl font-black uppercase text-sm tracking-[0.2em] shadow-xl hover:bg-slate-800 active:scale-95 transition-all">
                        Terminar Ahora
                    </button>
                </div>
                <script>setTimeout(() => {{ window.close(); }}, 3000);</script>
            </body>
            </html>
            """
            return HttpResponse(msg)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return HttpResponse(f"Error Técnico en la generación del PDF: {str(e)}", status=500)
