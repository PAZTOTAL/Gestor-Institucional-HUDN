import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.views import View
from xhtml2pdf import pisa
from .models import *

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="estudio_conveniencia.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
       return HttpResponse('Error al generar PDF: %s' % pisa_status.err, status=500)
    return response

class GenerarEstudioPDFView(View):
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        try:
            estudio = opsComponenteTecnico.objects.get(pk=pk)
        except opsComponenteTecnico.DoesNotExist:
            raise Http404("Estudio no encontrado")
            
        context = {
            'estudio': estudio,
            'condiciones': estudio.condiciones.first(),
            'obligaciones_generales': estudio.obligaciones_generales.all(),
            'obligaciones_especificas': estudio.obligaciones_especificas.all(),
            'aspectos_legales': estudio.aspectos_legales.all(),
            'aspectos_idoneidad': estudio.aspectos_idoneidad.all(),
            'aspectos_experiencia': estudio.aspectos_experiencia.all(),
            'formas_pago': estudio.valor_formas_pago.all(),
            'garantia': estudio.garantia if hasattr(estudio, 'garantia') else None,
            'dependencia': estudio.estado_dependencia if hasattr(estudio, 'estado_dependencia') else None,
            'viabilidad': estudio.estado_viabilidad if hasattr(estudio, 'estado_viabilidad') else None,
            'disponibilidad': estudio.disponibilidad if hasattr(estudio, 'disponibilidad') else None,
            'aceptacion': estudio.aceptacion_gerencia if hasattr(estudio, 'aceptacion_gerencia') else None,
        }
        
        return render_to_pdf('estudio_conveniencia/pdf.html', context)
