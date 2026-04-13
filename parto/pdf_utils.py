from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from django.http import HttpResponse
from django.conf import settings
from django.utils.timezone import localtime
import os


def encabezado(c, formulario, ancho, y):
    """
    Dibuja el encabezado institucional del PDF con logo, título y metadatos.
    Encabezado institucional (ESTÁTICO)
    
    Args:
        c: Canvas de reportlab
        formulario: Instancia del modelo Formulario
        ancho: Ancho de la página
        y: Posición Y inicial
    """
    # ORDEN: 1. Logo hospital (izquierda), 2. Título (centro), 3. Metadatos (derecha), 4. Logo acreditación (extrema derecha)
    
    # Definir márgenes y dimensiones del encabezado (basado en HTML)
    margen_encabezado_x = 0.5*cm
    margen_encabezado_y = 0.5*cm
    altura_encabezado = 3.2*cm
    y_top_encabezado = y
    y_bottom_encabezado = y - altura_encabezado
    
    # BORDE DEL ENCABEZADO (rectángulo completo - basado en .form-header border)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(margen_encabezado_x, y_bottom_encabezado, ancho - 2*margen_encabezado_x, altura_encabezado)
    
    # 1. LOGO HOSPITAL (izquierda - máximo a la izquierda posible)
    logo_hospital_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_hospital.png')
    logo_hospital_x = -0.5*cm
    logo_hospital_width = 6*cm
    logo_hospital_height = 1.8*cm
    
    if os.path.exists(logo_hospital_path):
        try:
            c.drawImage(
                logo_hospital_path,
                logo_hospital_x,
                y-2*cm,
                width=logo_hospital_width,
                height=logo_hospital_height,
                preserveAspectRatio=True
            )
        except:
            pass
    
    # LÍNEA VERTICAL 1: Después del logo hospital (basado en .header-left::after)
    # Logo termina aproximadamente en logo_hospital_x + logo_hospital_width = -0.5 + 6 = 5.5*cm
    # Línea va a la derecha del logo con gap de ~0.5cm
    linea1_x = 5.5*cm + 0.5*cm  # Después del logo
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(linea1_x, y_top_encabezado, linea1_x, y_bottom_encabezado)
    
    # 2. TÍTULO (cerca del logo del hospital, movido más a la izquierda)
    titulo_x = 4.5*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(titulo_x, y-0.5*cm, "CONTROL DE TRABAJO DE PARTO")
    
    # Calcular ancho del texto del título
    ancho_titulo = c.stringWidth("CONTROL DE TRABAJO DE PARTO", "Helvetica-Bold", 11)
    titulo_fin_x = titulo_x + ancho_titulo
    
    # LÍNEA VERTICAL 2: Después del título (basado en .header-center::after)
    # Línea va después del título con gap de ~0.5cm
    linea2_x = titulo_fin_x + 0.5*cm
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(linea2_x, y_top_encabezado, linea2_x, y_bottom_encabezado)
    
    # 3. METADATOS CÓDIGO/VERSIÓN (derecha, después del título)
    # Preparar datos de código y versión
    codigo_valor = formulario.codigo if formulario.codigo else "FRSPA-022"
    version_valor = formulario.version if formulario.version else "01"
    
    # Posición X para código/versión (más a la izquierda que las fechas)
    # Estas van después de la línea 2 (después del título)
    codigo_vers_x = linea2_x + 0.5*cm
    y_metadatos = y-0.5*cm
    
    # Dibujar CÓDIGO y VERSIÓN (textos estáticos con valores)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(codigo_vers_x, y_metadatos, "CÓDIGO")
    c.setFont("Helvetica", 8)
    c.drawString(codigo_vers_x + 2.5*cm, y_metadatos, codigo_valor)
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(codigo_vers_x, y_metadatos - 0.5*cm, "VERSIÓN")
    c.setFont("Helvetica", 8)
    c.drawString(codigo_vers_x + 2.5*cm, y_metadatos - 0.5*cm, version_valor)
    
    # Calcular el fin de la sección código/versión para la línea vertical
    ancho_codigo_vers = 5*cm  # Ancho aproximado de la sección código/versión
    fin_codigo_vers_x = codigo_vers_x + ancho_codigo_vers
    
    # 4. FECHAS DE ELABORACIÓN Y ACTUALIZACIÓN (en medio, entre código/versión y logo de acreditación)
    # Logo de acreditación está en: ancho - 2*cm - 3*cm
    logo_acreditacion_x = ancho - 2*cm - 3*cm
    
    # Calcular posición intermedia entre código/versión y logo de acreditación
    espacio_total = logo_acreditacion_x - fin_codigo_vers_x - 1*cm  # 1cm de margen para la línea
    fecha_elab_x = fin_codigo_vers_x + espacio_total / 2 - 2*cm  # Centrado aproximadamente
    y_fechas = y-0.5*cm
    
    # Dibujar las fechas (textos estáticos según el HTML)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(fecha_elab_x, y_fechas, "FECHA DE ELABORACIÓN")
    c.setFont("Helvetica", 7)
    c.drawString(fecha_elab_x, y_fechas - 0.4*cm, "2 DE MARZO DEL 2018")
    
    c.setFont("Helvetica-Bold", 7)
    c.drawString(fecha_elab_x, y_fechas - 1.0*cm, "FECHA DE ACTUALIZACIÓN")
    c.setFont("Helvetica", 7)
    c.drawString(fecha_elab_x, y_fechas - 1.4*cm, "2 DE MARZO DEL 2018")
    
    # Calcular fin de la sección de fechas para la línea vertical
    fin_fechas_x = fecha_elab_x + 4*cm  # Ancho aproximado de las fechas
    
    # LÍNEA VERTICAL 3: Entre código/versión y fechas (basado en .header-chip-side::before)
    linea3_x = fin_codigo_vers_x + 0.3*cm
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(linea3_x, y_top_encabezado, linea3_x, y_bottom_encabezado)
    
    # 5. LOGO ACREDITACIÓN (extrema derecha, parte superior)
    y_logo_acreditacion = y-2*cm
    logo_acreditacion_x = ancho - 2*cm - 3*cm
    
    logo_acreditacion_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_acreditacion.png')
    if os.path.exists(logo_acreditacion_path):
        try:
            c.drawImage(
                logo_acreditacion_path,
                logo_acreditacion_x,  # Extrema derecha
                y_logo_acreditacion,  # Parte superior del logo
                width=3*cm,
                height=2*cm,
                preserveAspectRatio=True
            )
        except:
            pass
    
    # LÍNEA VERTICAL 4: Antes del logo de acreditación (basado en .header-top-right::before)
    # Línea va antes del logo con gap de ~0.5cm
    linea4_x = logo_acreditacion_x - 0.5*cm
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(linea4_x, y_top_encabezado, linea4_x, y_bottom_encabezado)
    
    # Línea separadora horizontal (debajo de todo el encabezado)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(margen_encabezado_x, y_bottom_encabezado, ancho - margen_encabezado_x, y_bottom_encabezado)
    
    return y_bottom_encabezado


def casilla(c, x, y, w, h, etiqueta, valor=""):
    """
    Función casilla (BASE DEL FORMATO)
    Dibuja una casilla con etiqueta y valor.
    
    Args:
        c: Canvas de reportlab
        x: Posición X
        y: Posición Y
        w: Ancho de la casilla
        h: Alto de la casilla
        etiqueta: Texto de la etiqueta
        valor: Valor a mostrar (puede ser None)
    """
    c.rect(x, y, w, h)
    c.setFont("Helvetica", 7)
    c.drawString(x+4, y+h-10, etiqueta)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x+4, y+4, str(valor) if valor is not None else "")


def datos_paciente(c, formulario, x, y):
    """
    Datos del paciente (ESTRUCTURA)
    Dibuja los datos del paciente en el PDF usando casillas.
    
    Args:
        c: Canvas de reportlab
        formulario: Instancia del modelo Formulario
        x: Posición X (margen horizontal)
        y: Posición Y actual
    """
    p = formulario.paciente
    
    # Primera fila: Paciente (Nombres y Apellidos), Documento (Identificación)
    nombres = p.nombres or ""
    documento = p.num_identificacion or ""
    casilla(c, x, y, 9*cm, 1.2*cm, "Paciente", nombres)
    casilla(c, x+9*cm, y, 5*cm, 1.2*cm, "Documento", documento)
    
    # Segunda fila: Edad, Historia Clínica
    edad = formulario.edad_snapshot if formulario.edad_snapshot is not None else ""
    historia = p.num_historia_clinica or ""
    casilla(c, x, y-1.3*cm, 5*cm, 1.2*cm, "Edad", edad)
    casilla(c, x+5*cm, y-1.3*cm, 5*cm, 1.2*cm, "Historia", historia)
    
    # Tercera fila: Grupo Sanguíneo, Fecha de Nacimiento (si es necesario)
    grupo_sangre = p.tipo_sangre or ""
    fecha_nac = p.fecha_nacimiento.strftime('%d/%m/%Y') if p.fecha_nacimiento else ""
    casilla(c, x+10*cm, y-1.3*cm, 4*cm, 1.2*cm, "Grupo Sanguíneo", grupo_sangre)
    casilla(c, x, y-2.6*cm, 7*cm, 1.2*cm, "Fecha Nacimiento", fecha_nac)
    
    # Retornar nueva posición Y
    return y - 2.6*cm


def datos_formulario(c, margen_x, y, formulario):
    """
    Dibuja los datos del formulario en el PDF.
    
    Args:
        c: Canvas de reportlab
        margen_x: Margen horizontal
        y: Posición Y actual
        formulario: Instancia del modelo Formulario
    """
    # Título de sección
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor('#1f2937'))
    c.drawString(margen_x, y, "INFORMACIÓN DEL FORMULARIO")
    y -= 0.5*cm
    
    # Formatear fecha de actualización
    fecha_actualizacion_str = 'N/A'
    if formulario.fecha_actualizacion:
        fecha_actualizacion_str = formulario.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')
    
    # Datos del formulario
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    
    datos = [
        ('Código:', formulario.codigo or 'N/A'),
        ('Versión:', formulario.version or 'N/A'),
        ('Hoja:', str(formulario.num_hoja) if formulario.num_hoja else 'N/A'),
        ('Fecha de Elaboración:', formulario.fecha_elabora.strftime('%d/%m/%Y') if formulario.fecha_elabora else 'N/A'),
        ('Fecha de Actualización:', fecha_actualizacion_str),
        ('Aseguradora:', formulario.aseguradora.nombre if formulario.aseguradora else 'N/A'),
        ('Diagnóstico:', formulario.diagnostico or 'N/A'),
        ('Edad:', f'{formulario.edad_snapshot} años' if formulario.edad_snapshot else 'N/A'),
        ('Edad Gestacional:', f'{formulario.edad_gestion} semanas' if formulario.edad_gestion else 'N/A'),
        ('Estado (G_P_C_A_V_M):', formulario.get_estado_display() if formulario.estado else 'N/A'),
        ('N° Controles Prenatales:', str(formulario.n_controles_prenatales) if formulario.n_controles_prenatales else 'N/A'),
        ('Responsable:', formulario.responsable or 'N/A'),
    ]
    
    for etiqueta, valor in datos:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margen_x, y, etiqueta)
        ancho_etiqueta = c.stringWidth(etiqueta, "Helvetica-Bold", 10)
        c.setFont("Helvetica", 10)
        # Si el valor es muy largo, dividirlo en múltiples líneas
        valor_str = str(valor)
        if len(valor_str) > 50:
            palabras = valor_str.split()
            linea = ""
            for palabra in palabras:
                if len(linea + palabra) > 50:
                    c.drawString(margen_x + ancho_etiqueta + 0.2*cm, y, linea)
                    y -= 0.4*cm
                    linea = palabra + " "
                else:
                    linea += palabra + " "
            if linea:
                c.drawString(margen_x + ancho_etiqueta + 0.2*cm, y, linea)
        else:
            c.drawString(margen_x + ancho_etiqueta + 0.2*cm, y, valor_str)
        y -= 0.5*cm
    
    return y


def obtener_valor(valor):
    """
    Obtiene el valor de MedicionValor según su tipo.
    
    Args:
        valor: Instancia de MedicionValor
    
    Returns:
        str: Representación del valor
    """
    if valor.valor_number is not None:
        return str(valor.valor_number)
    if valor.valor_text is not None:
        return valor.valor_text
    if valor.valor_boolean is not None:
        return "Sí" if valor.valor_boolean else "No"
    if valor.valor_json is not None:
        return str(valor.valor_json)
    return ""


def seccion_grid_mediciones(c, formulario, x, y, ancho_total):
    """
    Dibuja el grid de mediciones estilo formulario (12 columnas de tiempo).
    """
    from .models import Item, Medicion, MedicionValor
    
    # 1. Obtener mediciones agrupadas por hora
    mediciones = Medicion.objects.filter(formulario=formulario).prefetch_related('valores__campo', 'parametro')
    horas_unicas = sorted(list(set(m.tomada_en for m in mediciones)))
    
    # Limitar a 10 horas para el grid
    horas_mostrar = horas_unicas[:10]
    
    # 2. Definir anchos de columna
    col_item = 2.5*cm
    col_param = 3.5*cm
    col_hora = (ancho_total - col_item - col_param - 1*cm) / 10
    
    # 3. Dibujar Encabezado del Grid
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.lightgrey)
    c.rect(x, y-1*cm, ancho_total - 1*cm, 1*cm, fill=1)
    c.setFillColor(colors.black)
    
    c.drawString(x + 0.2*cm, y-0.6*cm, "ITEM")
    c.drawString(x + col_item + 0.2*cm, y-0.6*cm, "PARÁMETRO")
    
    # Dibujar Horas
    for i, hora in enumerate(horas_mostrar):
        hora_str = hora.strftime('%H:%M')
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x + col_item + col_param + (i * col_hora) + col_hora/2, y-0.6*cm, hora_str)
    
    y -= 1*cm
    
    # 4. Dibujar Filas por Item/Parámetro
    items = Item.objects.prefetch_related('parametros__campos').all().order_by('id')
    
    for item in items:
        # Título de Sección (Item)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.HexColor('#d1d5db'))
        c.rect(x, y-0.6*cm, ancho_total - 1*cm, 0.6*cm, fill=1)
        c.setFillColor(colors.black)
        c.drawString(x + 0.5*cm, y-0.4*cm, item.nombre.upper())
        y -= 0.6*cm
        
        for param in item.parametros.all():
            campos = param.campos.all()
            altura_fila = max(0.6*cm, 0.4*cm * campos.count())
            
            # Borde de la fila
            c.rect(x, y-altura_fila, ancho_total - 1*cm, altura_fila)
            
            # Nombre del Parámetro
            c.setFont("Helvetica", 7)
            c.drawString(x + col_item + 0.2*cm, y - 0.4*cm, param.nombre.upper())
            
            # Dibujar Valores para cada hora
            for i, hora in enumerate(horas_mostrar):
                medicion_h = next((m for m in mediciones if m.tomada_en == hora and m.parametro_id == param.id), None)
                
                if medicion_h:
                    for idx_c, campo in enumerate(campos):
                        valor_obj = next((v for v in medicion_h.valores.all() if v.campo_id == campo.id), None)
                        if valor_obj:
                            texto_v = obtener_valor(valor_obj)
                            c.setFont("Helvetica", 6)
                            # Ajustar posición si hay múltiples campos
                            offset_y = (idx_c * 0.3*cm) if campos.count() > 1 else 0
                            c.drawCentredString(x + col_item + col_param + (i * col_hora) + col_hora/2, y - 0.4*cm - offset_y, texto_v)
            
            y -= altura_fila
            
            # Control de página
            if y < 3*cm:
                c.showPage()
                y = A4[1] - 2*cm
                # (Opcional: repetir encabezado si se desea)

    return y


def seccion_mediciones(c, formulario, x, y):
    """
    Sección completa de mediciones (CLAVE)
    Recorre todas las mediciones, todos los campos, respeta el tipo de valor.
    No se pierde nada.
    
    Args:
        c: Canvas de reportlab
        formulario: Instancia del modelo Formulario
        x: Posición X (margen horizontal)
        y: Posición Y actual
    """
    from .models import Medicion
    
    # Obtener todas las mediciones del formulario
    mediciones = (
        Medicion.objects
        .filter(formulario=formulario)
        .select_related("parametro")
        .prefetch_related("valores__campo")
        .order_by("parametro__orden", "tomada_en")
    )
    
    if not mediciones.exists():
        c.setFont("Helvetica", 10)
        c.drawString(x, y, "No hay mediciones registradas.")
        return y - 0.5*cm
    
    # Recorrer todas las mediciones
    for medicion in mediciones:
        # TÍTULO DEL PARÁMETRO
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, medicion.parametro.nombre)
        y -= 0.5*cm
        
        # Crear tabla con encabezados
        data = [["Campo", "Valor", "Unidad"]]
        
        # Agregar todos los valores de la medición
        for v in medicion.valores.all():
            data.append([
                v.campo.nombre,
                obtener_valor(v),
                v.campo.unidad or ""
            ])
        
        # Crear tabla con reportlab
        tabla = Table(data, colWidths=[6*cm, 5*cm, 3*cm])
        tabla.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Dibujar la tabla
        tabla.wrapOn(c, 0, 0)
        tabla.drawOn(c, x, y - len(data) * 0.6*cm)
        
        # Actualizar posición Y
        y -= (len(data) + 2) * 0.6*cm
        
        # Control de paginación
        if y < 4*cm:
            c.showPage()
            y = A4[1] - 2*cm
    
    return y


def generar_pdf_formulario_clinico(formulario, response=None):
    """
    Genera un PDF del formulario clínico con toda su información.
    Estructura base del PDF (OBLIGATORIO)
    
    Args:
        formulario: Instancia del modelo Formulario
        response: HttpResponse opcional para descargar directamente
    
    Returns:
        HttpResponse con el PDF generado
    """
    # Crear el buffer para el PDF
    if response is None:
        response = HttpResponse(content_type='application/pdf')
    
    # Nombre del archivo
    nombre_archivo = f"formulario_{formulario.codigo}_v{formulario.version}_hoja{formulario.num_hoja}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    # Crear el canvas del PDF
    c = canvas.Canvas(response, pagesize=A4)
    
    ancho, alto = A4
    margen_x = 2*cm
    y = alto - 2*cm
    
    # Estructura base del PDF (OBLIGATORIO)
    y = encabezado(c, formulario, ancho, y)
    y -= 1*cm
    
    y = datos_paciente(c, formulario, margen_x, y)
    y -= 1*cm
    
    y = datos_formulario(c, margen_x, y, formulario)
    y -= 1*cm
    
    y = seccion_mediciones(c, formulario, margen_x, y)
    
    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    fecha_generacion = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    texto_footer = f"Generado el {fecha_generacion}"
    ancho_footer = c.stringWidth(texto_footer, "Helvetica", 8)
    c.drawString((ancho - ancho_footer) / 2, 1.5*cm, texto_footer)
    
    c.showPage()
    c.save()
    
    return response


def generar_pdf_simple(nombre_archivo, contenido, response=None):
    """
    Función simple para generar PDFs básicos (versión original adaptada).
    
    Args:
        nombre_archivo: Nombre del archivo PDF
        contenido: Contenido de texto para el PDF
        response: HttpResponse opcional
    
    Returns:
        HttpResponse con el PDF generado
    """
    if response is None:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    # Crear el archivo PDF
    c = canvas.Canvas(response, pagesize=letter)
    
    # Definir las posiciones y el contenido del PDF
    c.drawString(100, 750, contenido)
    
    # Guardar el PDF generado
    c.save()
    
    return response

