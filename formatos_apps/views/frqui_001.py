from django.views.generic import CreateView, ListView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from ..models import FRQUI_001_Model
from ..forms import FRQUI_001_Form
from BasesGenerales.models import Formatos_Hudn
from core.mixins import AccessControlMixin
from .base import render_pdf_with_template

class FRQUI_001_CreateView(AccessControlMixin, CreateView):
    model = FRQUI_001_Model
    form_class = FRQUI_001_Form
    template_name = 'formatos_apps/frqui_001_form.html'
    success_url = reverse_lazy('formatos_apps:frqui_001_list')
    permission_type = 'add'

    def get(self, request, *args, **kwargs):
        db_choice = request.GET.get('db')
        if db_choice in ['readonly', 'nexus']:
            request.session['hospital_db'] = db_choice
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_db'] = self.request.session.get('hospital_db', 'readonly')
        context['is_update'] = False
        return context

    def form_valid(self, form):
        form.instance.usuario_registro = self.request.user
        form.instance.formato_maestro = get_object_or_404(Formatos_Hudn, codigo_formato='FRQUI-001')
        return super().form_valid(form)

class FRQUI_001_UpdateView(FRQUI_001_CreateView, UpdateView):
    permission_type = 'change'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

class FRQUI_001_ListView(AccessControlMixin, ListView):
    model = FRQUI_001_Model
    template_name = 'formatos_apps/frqui_001_list.html'
    context_object_name = 'registros'
    permission_type = 'view'

def generar_pdf_frqui_001(request, pk):
    registro = get_object_or_404(FRQUI_001_Model, pk=pk)
    
    def draw_content(can):
        can.setFont("Helvetica-Bold", 8)
        # Información General (Consolidada, sin EPS, desplazada a la derecha y bajada)
        paciente_info = f"{registro.paciente_nombre or ''}  |  CC: {registro.identificacion_paciente or ''}  |  HC: {registro.atencion_codigo or ''}"
        can.drawString(160, 685, paciente_info)
        fecha_str = registro.fecha_registro.strftime("%d/%m/%Y") if registro.fecha_registro else ""
        hora_str = registro.hora_egreso.strftime("%H:%M") if registro.hora_egreso else ""
        can.drawString(100, 660, f"{fecha_str}   {hora_str}")

        # SECCIÓN 1
        y_start = 635
        items_sec1 = [
            'camilla_transporte', 'confirma_identificacion', 'cesarea_identificacion',
            'puntaje_aldrete', 'puntaje_bromage', 'escala_dolor', 'condiciones_clinicas',
            'plan_tratamiento', 'kardex_tarjetas', 'paciente_comentado', 'acceso_venoso',
            'herida_quirurgica', 'tubos_drenes', 'limpieza_piel'
        ]
        for i, item in enumerate(items_sec1):
            y_pos = y_start - (i * 12.8)
            status = getattr(registro, f"{item}_status")
            obs = getattr(registro, f"{item}_obs") or ""
            if status == 'SI': can.drawString(310, y_pos, "X")
            elif status == 'NO': can.drawString(330, y_pos, "X")
            elif status == 'NA': can.drawString(355, y_pos, "X")
            can.drawString(425, y_pos, obs[:35])

        # Firmas Auxiliares (Aproximado)
        can.drawString(100, 425, registro.auxiliar_entrega_nombre or "")
        can.drawString(400, 425, registro.auxiliar_recibe_nombre or "")

        # SECCIÓN 2
        y_start_sec2 = 375
        items_sec2 = [
            'historia_descripcion', 'historia_anestesia', 'historia_escalas',
            'historia_formula', 'historia_consentimiento', 'historia_triple_tarjeta',
            'historia_lista_instrumentacion'
        ]
        for i, item in enumerate(items_sec2):
            # Ajuste individual por fila para máxima precisión
            if i == 0:
                offset = 3
            elif i == 1:
                offset = 5
            elif i == 2:
                offset = 6
            elif i == 3:
                offset = 7
            elif i == 4:
                offset = 9
            elif i == 5:
                offset = 11
            else:
                offset = 12
            y_pos = y_start_sec2 - (i * 13.5) + offset
            
            status = getattr(registro, f"{item}_status")
            if status == 'SI': can.drawString(310, y_pos, "X")
            elif status == 'NO': can.drawString(330, y_pos, "X")
            elif status == 'NA': can.drawString(355, y_pos, "X")

        # Firmas Enfermería (Aproximado)
        can.drawString(100, 278, registro.enfermeria_entrega_nombre or "")
        can.drawString(400, 278, registro.enfermeria_recibe_nombre or "")

        # SECCIÓN 3
        y_start_sec3 = 194
        items_sec3 = [
            'amb_nombre_medico', 'amb_fecha_control', 'amb_formula_explicacion',
            'amb_cuidados_casa', 'amb_instructivo_cuidados', 'amb_recomendaciones_alarmas',
            'amb_rayos_x_otros', 'amb_triple_tarjeta'
        ]
        for i, item in enumerate(items_sec3):
            # La fila 4 (índice 3) tiene doble altura en el papel.
            # Ajustamos la X de la fila 4 y desplazamos el resto hacia abajo.
            if i < 3:
                y_pos = y_start_sec3 - (i * 13.5)
            elif i == 3:
                y_pos = y_start_sec3 - (i * 13.5) - 6  # Centrar en fila doble
            elif i < 6:
                # Items 5 y 6 (índices 4-5)
                y_pos = y_start_sec3 - (i * 13.5) - 10
            elif i == 6:
                # Item 7
                y_pos = y_start_sec3 - (i * 13.5) - 7
            else:
                # Item 8: Subimos 3 puntos más (-7 + 3 = -4)
                y_pos = y_start_sec3 - (i * 13.5) - 4
            
            status = getattr(registro, f"{item}_status")
            if status == 'SI': can.drawString(310, y_pos, "X")
            elif status == 'NO': can.drawString(330, y_pos, "X")
            elif status == 'NA': can.drawString(355, y_pos, "X")

        # Firmas Finales
        can.drawString(100, 60, registro.firma_usuario_familiar or "")
        can.drawString(400, 60, registro.firma_enfermera_nombre or "")

    return render_pdf_with_template(
        'FRQUI-001_Template.pdf',
        draw_content,
        f"FRQUI-001_{registro.identificacion_paciente}",
        request
    )
