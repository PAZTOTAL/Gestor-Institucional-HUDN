from django.views.generic import CreateView, ListView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from ..models import FRQUI_095_Model
from BasesGenerales.models import Formatos_Hudn
from core.mixins import AccessControlMixin
from .base import render_pdf_with_template

class FRQUI_095_CreateView(AccessControlMixin, CreateView):
    model = FRQUI_095_Model
    template_name = 'formatos_apps/frqui_095_form.html'
    fields = [
        'identificacion_paciente', 'paciente_nombre', 'atencion_codigo', 'eps', 'fecha_operacion',
        'cirujano_id', 'cirujano_nombre', 'ayudante_id', 'ayudante_nombre',
        'anestesiologo_id', 'anestesiologo_nombre', 'auxiliar_id', 'auxiliar_nombre',
        'diagnostico', 'procedimiento',
        'clasificacion_herida', 'electrobisturi', 'sitio_ubicacion_placa',
        'indicador_quimico', 'indicador_quimico_interno', 'indicador_quimico_externo', 'indicador_biologico',
        'compresas_inicial', 'compresas_final', 'compresas_na', 'compresas_responsable_id', 'compresas_responsable_nombre', 'compresas_observacion',
        'gasas_inicial', 'gasas_final', 'gasas_na', 'gasas_responsable_id', 'gasas_responsable_nombre', 'gasas_observacion',
        'torundas_inicial', 'torundas_final', 'torundas_na', 'torundas_responsable_id', 'torundas_responsable_nombre', 'torundas_observacion',
        'pinzas_inicial', 'pinzas_final', 'pinzas_na', 'pinzas_responsable_id', 'pinzas_responsable_nombre', 'pinzas_observacion',
        'tetras_inicial', 'tetras_final', 'tetras_na', 'tetras_responsable_id', 'tetras_responsable_nombre', 'tetras_observacion',
        'agujas_inicial', 'agujas_final', 'agujas_na', 'agujas_responsable_id', 'agujas_responsable_nombre', 'agujas_observacion',
        'cotonoides_inicial', 'cotonoides_final', 'cotonoides_na', 'cotonoides_responsable_id', 'cotonoides_responsable_nombre', 'cotonoides_observacion',
        'hoja_bisturi_inicial', 'hoja_bisturi_final', 'hoja_bisturi_na', 'hoja_bisturi_responsable_id', 'hoja_bisturi_responsable_nombre', 'hoja_bisturi_observacion',
        'mechas_inicial', 'mechas_final', 'mechas_na', 'mechas_responsable_id', 'mechas_responsable_nombre', 'mechas_observacion',
        'vendas_gasa_inicial', 'vendas_gasa_final', 'vendas_gasa_na', 'vendas_gasa_responsable_id', 'vendas_gasa_responsable_nombre', 'vendas_gasa_observacion',
    ]
    success_url = reverse_lazy('formatos_apps:frqui_095_list')
    permission_type = 'add'

    def get(self, request, *args, **kwargs):
        db_choice = request.GET.get('db')
        if db_choice in ['readonly', 'nexus']:
            request.session['hospital_db'] = db_choice
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materials_list'] = [
            ('compresas', 'Compresas'),
            ('gasas', 'GasaS'),
            ('torundas', 'Torundas'),
            ('pinzas', 'Pinzas'),
            ('tetras', 'Tetras'),
            ('agujas', 'Agujas'),
            ('cotonoides', 'Cotonoides'),
            ('hoja_bisturi', 'Hoja bisturi'),
            ('mechas', 'Mechas'),
            ('vendas_gasa', 'Vendas de gasa'),
        ]
        context['selected_db'] = self.request.session.get('hospital_db', 'readonly')
        context['is_update'] = False
        return context

    def form_valid(self, form):
        form.instance.usuario_registro = self.request.user
        form.instance.formato_maestro = get_object_or_404(Formatos_Hudn, codigo_formato='FRQUI-095')
        return super().form_valid(form)

class FRQUI_095_UpdateView(FRQUI_095_CreateView, UpdateView):
    permission_type = 'change'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

class FRQUI_095_ListView(AccessControlMixin, ListView):
    model = FRQUI_095_Model
    template_name = 'formatos_apps/frqui_095_list.html'
    context_object_name = 'registros'
    permission_type = 'view'

def generar_pdf_frqui_095(request, pk):
    registro = get_object_or_404(FRQUI_095_Model, pk=pk)
    
    def draw_content(can):
        can.setFont("Helvetica-Bold", 8)
        # Cabecera
        can.drawString(80, 720, registro.identificacion_paciente or "")
        can.drawString(86, 703, registro.atencion_codigo or "")
        can.drawString(255, 703, registro.eps or "")
        can.drawString(420, 703, str(registro.fecha_operacion or ""))
        
        can.drawString(100, 685, registro.paciente_nombre or "")
        can.drawString(60, 670, registro.cirujano_nombre or "")
        can.drawString(330, 670, registro.ayudante_nombre or "")
        can.drawString(65, 655, registro.anestesiologo_nombre or "")
        can.drawString(370, 655, registro.auxiliar_nombre or "")
        
        can.drawString(70, 640, (registro.diagnostico or "")[:100])
        can.drawString(72, 624, (registro.procedimiento or "")[:100])
        
        # Herida
        herida_coords = {'LIMPIA': (235, 595), 'CONTAMINADA': (395, 595), 'LIMPIA_CONTAMINADA': (235, 580), 'SUCIA': (395, 580)}
        if registro.clasificacion_herida in herida_coords:
            cx, cy = herida_coords[registro.clasificacion_herida]
            can.drawString(cx, cy, "X")

        if registro.electrobisturi: can.drawString(105, 555, "X")
        can.drawString(370, 555, registro.sitio_ubicacion_placa or "")

        # Indicadores
        if registro.indicador_quimico: can.drawString(105, 525, "X")
        if registro.indicador_quimico_interno: can.drawString(245, 525, "X")
        if registro.indicador_quimico_externo: can.drawString(380, 525, "X")
        if registro.indicador_biologico: can.drawString(525, 525, "X")

        # Conteo (Ejemplo simplificado de una fila)
        # ... Aquí iría el resto de la lógica de dibujo de FRQUI-095 ...
        pass

    return render_pdf_with_template(
        'FRQUI-095_Template.pdf',
        draw_content,
        f"FRQUI-095_{registro.identificacion_paciente}",
        request
    )
