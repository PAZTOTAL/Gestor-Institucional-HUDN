import io
import os
from django.conf import settings
from django.http import HttpResponse
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def render_pdf_with_template(template_name, draw_callback, filename_prefix, request):
    """
    Función utilitaria para generar PDFs sobre una plantilla maestra.
    - template_name: nombre del archivo en pdf_templates (ej: 'FRQUI-095_Template.pdf')
    - draw_callback: función que recibe el objeto 'canvas' para dibujar los datos.
    - filename_prefix: prefijo para el nombre del archivo descargado.
    """
    template_path = os.path.join(settings.BASE_DIR, 'formatos_apps', 'pdf_templates', template_name)
    
    if not os.path.exists(template_path):
        return HttpResponse(f"Error: No se encuentra la plantilla PDF en {template_path}.", status=404)

    try:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica-Bold", 8)
        
        # MODO CALIBRACIÓN (Universal para todos los formatos)
        if request.GET.get('calibrate'):
            can.setFont("Helvetica", 6)
            can.setStrokeColorRGB(0.8, 0.8, 0.8)
            for x in range(0, 600, 50):
                can.line(x, 0, x, 800)
                for y in range(0, 800, 20):
                    can.drawString(x, y, f"{x},{y}")
            for y in range(0, 800, 50):
                can.line(0, y, 600, y)

        # Ejecutar la lógica específica del formato
        draw_callback(can)

        can.save()
        packet.seek(0)
        
        new_pdf = PdfReader(packet)
        with open(template_path, "rb") as f_template:
            existing_pdf = PdfReader(f_template)
            output = PdfWriter()
            
            # Asumimos que es un PDF de una sola página (estándar institucional)
            page = existing_pdf.pages[0]
            page.merge_page(new_pdf.pages[0])
            output.add_page(page)
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename_prefix}.pdf"'
            output.write(response)
            return response

    except Exception as e:
        import traceback
        return HttpResponse(f"Error Técnico en la generación del PDF: {str(e)}<pre>{traceback.format_exc()}</pre>", status=500)
