"""
Generador de PDF MEOWS usando ReportLab - Formato idéntico al formato físico
"""
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import os


def obtener_rangos_por_score(parametro_codigo):
    """
    Obtiene los rangos de valores organizados por score para un parámetro.
    Retorna un diccionario: {score: [(min, max), ...]}
    """
    from meows.models import Parametro, RangoParametro
    
    try:
        parametro = Parametro.objects.get(codigo=parametro_codigo, activo=True)
        rangos = RangoParametro.objects.filter(
            parametro=parametro,
            activo=True
        ).order_by('orden', 'valor_min')
        
        rangos_por_score = {}
        for rango in rangos:
            if rango.score not in rangos_por_score:
                rangos_por_score[rango.score] = []
            rangos_por_score[rango.score].append((float(rango.valor_min), float(rango.valor_max)))
        
        return rangos_por_score
    except Parametro.DoesNotExist:
        return {}


def obtener_color_score(score):
    """Retorna el color correspondiente al score"""
    colores = {
        0: colors.white,      # Blanco - 0 puntos
        1: colors.HexColor('#00b050'),  # Verde - 1 punto
        2: colors.HexColor('#ffff00'),  # Amarillo - 2 puntos
        3: colors.HexColor('#ff0000'),  # Rojo - 3 puntos
    }
    return colores.get(score, colors.white)


def generar_pdf_meows(paciente, mediciones):
    """
    Genera un PDF MEOWS con formato idéntico al formato físico usando ReportLab.
    
    Args:
        paciente: Instancia del modelo Paciente
        mediciones: QuerySet de Medicion ordenadas por fecha_hora
    
    Returns:
        HttpResponse con el PDF generado
    """
    if not mediciones.exists():
        return HttpResponse("No hay mediciones para generar el PDF", status=400)
    
    # DEFINIR VARIABLES DE ANCHO AL INICIO para evitar errores de variable no definida
    ancho_puntos = 1.1*cm  # Valor por defecto - definir primero
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    
    # Crear documento en formato landscape (horizontal)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=0.8*cm,
        leftMargin=0.8*cm,
        topMargin=0.8*cm,
        bottomMargin=0.8*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=10,
        textColor=colors.black,
        alignment=1,  # Centrado
        spaceAfter=6,
    )
    estilo_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black,
    )
    estilo_datos = ParagraphStyle(
        'Datos',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.black,
        alignment=1,  # Centrado
        leading=9,  # Espaciado entre líneas
    )
    estilo_valor_celda = ParagraphStyle(
        'ValorCelda',
        parent=styles['Normal'],
        fontSize=6.5,  # Reducido para evitar desbordamiento
        textColor=colors.black,
        alignment=1,  # Centrado
        leading=8,  # Espaciado entre líneas reducido
        spaceAfter=0,
        spaceBefore=0,
    )
    
    # Contenedor de elementos
    story = []
    
    # ===== ENCABEZADO PROFESIONAL =====
    # Logo izquierdo (si existe)
    logo_izq_path = ''
    if settings.STATICFILES_DIRS:
        logo_izq_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'logo_hospital.png')
        if not os.path.exists(logo_izq_path):
            logo_izq_path = ''
    
    # Logo derecho (si existe)
    logo_der_path = ''
    if settings.STATICFILES_DIRS:
        logo_der_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'logo_acreditacion.png')
        if not os.path.exists(logo_der_path):
            logo_der_path = ''
    
    # Estilos para el encabezado - aumentados para aprovechar el espacio ampliado
    estilo_titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Normal'],
        fontSize=12,  # Más grande con más espacio
        textColor=colors.black,
        alignment=1,  # Centrado
        spaceAfter=3,
        spaceBefore=0,
        fontName='Helvetica-Bold',
        leading=14,
    )
    
    estilo_subtitulo_meows = ParagraphStyle(
        'SubtituloMeows',
        parent=styles['Normal'],
        fontSize=11,  # Más grande
        textColor=colors.black,
        alignment=1,  # Centrado
        spaceAfter=3,
        spaceBefore=0,
        fontName='Helvetica-Bold',
        leading=13,
    )
    
    estilo_codigo_version = ParagraphStyle(
        'CodigoVersion',
        parent=styles['Normal'],
        fontSize=8,  # Más grande
        textColor=colors.black,
        alignment=1,  # Centrado
        spaceAfter=0,
        spaceBefore=0,
        fontName='Helvetica',
        leading=10,
    )
    
    estilo_fechas = ParagraphStyle(
        'Fechas',
        parent=styles['Normal'],
        fontSize=7.5,  # Más grande
        textColor=colors.black,
        alignment=2,  # Derecha
        spaceAfter=2,
        spaceBefore=0,
        fontName='Helvetica',
        leading=9,
    )
    
    estilo_nombre_hospital = ParagraphStyle(
        'NombreHospital',
        parent=styles['Normal'],
        fontSize=8,  # Más grande
        textColor=colors.black,
        alignment=0,  # Izquierda
        spaceAfter=3,
        spaceBefore=3,
        fontName='Helvetica',
        leading=11,
    )
    
    # Construir encabezado con estructura organizada y sin superposición
    encabezado_data = []
    
    # Columna izquierda - Logo y nombre del hospital (más amplia)
    columna_izq = []
    if logo_izq_path and os.path.exists(logo_izq_path):
        try:
            img_izq = Image(logo_izq_path, width=5.5*cm, height=2.2*cm)  # Logo más grande
            columna_izq.append(img_izq)
        except:
            pass
    
    # Nombre del hospital: primera línea en negrita, segunda normal
    nombre_hospital = Paragraph(
        "<b>HOSPITAL UNIVERSITARIO</b><br/>"
        "DEPARTAMENTAL DE NARIÑO E.S.E.",
        estilo_nombre_hospital
    )
    columna_izq.append(nombre_hospital)
    
    # Columna centro - Título principal, subtítulo y código/versión (cada uno en su propia estructura)
    columna_centro = []
    # Título principal
    titulo_principal = Paragraph(
        "<b>SISTEMA ALERTA TEMPRANA OBSTÉTRICO</b>",
        estilo_titulo_principal
    )
    columna_centro.append(titulo_principal)
    
    # Subtítulo MEOWS
    subtitulo_meows = Paragraph(
        "<b>(MEOWS)</b>",
        estilo_subtitulo_meows
    )
    columna_centro.append(subtitulo_meows)
    
    # Código y versión
    codigo_version = Paragraph(
        "<b>CÓDIGO:</b> FRSPA-026 · <b>VERSIÓN:</b> 01",
        estilo_codigo_version
    )
    columna_centro.append(codigo_version)
    
    # Columna derecha - Fechas y logo de acreditación
    columna_derecha = []
    # Fechas en líneas separadas para mejor legibilidad
    fecha_elaboracion = Paragraph(
        "<b>FECHA DE ELABORACIÓN:</b> 27 DE DICIEMBRE DE 2023",
        estilo_fechas
    )
    columna_derecha.append(fecha_elaboracion)
    
    fecha_actualizacion = Paragraph(
        "<b>FECHA DE ACTUALIZACIÓN:</b> 27 DE DICIEMBRE DE 2023",
        estilo_fechas
    )
    columna_derecha.append(fecha_actualizacion)
    
    hoja = Paragraph(
        "<b>HOJA</b> 1 DE 2",
        estilo_fechas
    )
    columna_derecha.append(hoja)
    
    if logo_der_path and os.path.exists(logo_der_path):
        try:
            img_der = Image(logo_der_path, width=4.5*cm, height=1.5*cm)  # Logo más grande
            columna_derecha.append(img_der)
        except:
            pass
    
    # Crear la fila principal con las tres columnas organizadas
    fila_superior = [columna_izq, columna_centro, columna_derecha]
    encabezado_data.append(fila_superior)
    
    # Crear tabla principal del encabezado ENCAPSULADA EN CASILLAS (con bordes visibles)
    # Anchos MUY AMPLIADOS: total aproximado 27cm (ancho landscape A4 - márgenes)
    tabla_encabezado = Table(encabezado_data, colWidths=[8*cm, 11*cm, 8*cm])
    tabla_encabezado.setStyle(TableStyle([
        # Bordes externos completos (casilla encapsulada)
        ('BOX', (0, 0), (-1, -1), 1, colors.black),  # Borde exterior completo
        
        # Líneas verticales internas (separan las 3 columnas)
        ('LINEAFTER', (0, 0), (0, -1), 1, colors.black),  # Línea vertical después de columna 1
        ('LINEAFTER', (1, 0), (1, -1), 1, colors.black),  # Línea vertical después de columna 2
        
        # Línea inferior gruesa (separador principal)
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.black),
        
        # Alineación por columna - CRÍTICO para evitar superposición
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Columna izquierda: logo y nombre - alineado a la izquierda
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Columna centro: título - centrado
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),  # Columna derecha: fechas - alineado a la derecha
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alineación vertical arriba para mejor distribución
        
        # Padding interno MUY GENEROSO para aprovechar el espacio ampliado
        ('LEFTPADDING', (0, 0), (0, 0), 15),  # Columna izquierda - más espacio
        ('LEFTPADDING', (1, 0), (1, 0), 12),  # Columna centro - más espacio
        ('LEFTPADDING', (2, 0), (2, 0), 12),  # Columna derecha - más espacio
        ('RIGHTPADDING', (0, 0), (0, 0), 12),
        ('RIGHTPADDING', (1, 0), (1, 0), 12),
        ('RIGHTPADDING', (2, 0), (2, 0), 15),  # Columna derecha más padding
        ('TOPPADDING', (0, 0), (-1, -1), 12),  # Más espacio vertical
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),  # Más espacio vertical
        
        # Fondo blanco
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    
    story.append(tabla_encabezado)
    story.append(Spacer(1, 0.4*cm))
    
    # ===== DATOS DEL PACIENTE =====
    # Estilo para datos del paciente - Tamaños reducidos para que quepa todo
    estilo_label_datos = ParagraphStyle(
        'LabelDatos',
        parent=styles['Normal'],
        fontSize=6.5,  # Reducido de 7 a 6.5
        textColor=colors.black,
        alignment=0,  # Izquierda
        fontName='Helvetica-Bold',
        leading=8,  # Espaciado reducido
        spaceAfter=0,
        spaceBefore=0,
    )
    
    estilo_valor_datos = ParagraphStyle(
        'ValorDatos',
        parent=styles['Normal'],
        fontSize=6.5,  # Reducido de 7 a 6.5
        textColor=colors.black,
        alignment=0,  # Izquierda
        fontName='Helvetica',
        leading=8,  # Espaciado reducido
        spaceAfter=0,
        spaceBefore=0,
    )
    
    # Preparar datos con Paragraph para mejor control de texto largo
    nombre_completo = f"{paciente.nombres} {paciente.apellidos}".strip() or '-'
    edad_texto = f"{paciente.edad} años" if paciente.edad else '-'
    aseguradora_texto = paciente.aseguradora or '-'
    cama_texto = paciente.cama or '-'
    identificacion_texto = paciente.numero_documento
    fecha_ingreso_texto = paciente.fecha_ingreso.strftime('%d/%m/%Y') if paciente.fecha_ingreso else '-'
    
    datos_paciente = [
        [
            Paragraph('NOMBRE<br/>COMPLETO', estilo_label_datos),  # Dividido en 2 líneas
            Paragraph(nombre_completo, estilo_valor_datos),
            Paragraph('EDAD', estilo_label_datos),
            Paragraph(edad_texto, estilo_valor_datos),
            Paragraph('ASEGURADORA', estilo_label_datos),
            Paragraph(aseguradora_texto, estilo_valor_datos)
        ],
        [
            Paragraph('CAMA', estilo_label_datos),
            Paragraph(cama_texto, estilo_valor_datos),
            Paragraph('IDENTIF.<br/>CACIÓN', estilo_label_datos),  # Dividido en 2 líneas
            Paragraph(identificacion_texto, estilo_valor_datos),
            Paragraph('FECHA DE<br/>INGRESO', estilo_label_datos),  # Dividido en 2 líneas
            Paragraph(fecha_ingreso_texto, estilo_valor_datos)
        ],
    ]
    
    # Calcular anchos proporcionales - ajustar para que todo quepa bien
    ancho_total_datos = landscape(A4)[0] - 1.6*cm
    
    # Distribución optimizada: labels más estrechos, valores con espacio adecuado
    # Usar anchos uniformes para cada posición de columna
    ancho_label = 2.1*cm  # Labels en columnas 0, 2, 4 (más estrecho porque ahora tienen <br/>)
    
    # Calcular anchos para valores según el más largo de cada columna
    # Columna 1: nombre o cama (nombre es más largo)
    ancho_col1 = 3.8*cm
    # Columna 3: edad o identificación (identificación puede ser más larga)
    ancho_col3 = 2.8*cm
    # Columna 5: aseguradora o fecha (aseguradora es más larga)
    ancho_col5 = 4.5*cm
    
    # Verificar que la suma de anchos no exceda el total disponible
    ancho_total_necesario = (ancho_label * 3) + ancho_col1 + ancho_col3 + ancho_col5
    
    # Ajustar proporcionalmente si excede
    if ancho_total_necesario > ancho_total_datos:
        factor_reduccion = ancho_total_datos / ancho_total_necesario
        ancho_label *= factor_reduccion
        ancho_col1 *= factor_reduccion
        ancho_col3 *= factor_reduccion
        ancho_col5 *= factor_reduccion
    
    # Crear tabla con anchos calculados
    tabla_datos = Table(datos_paciente, colWidths=[
        ancho_label,  # Col 0: Labels (NOMBRE COMPLETO, CAMA)
        ancho_col1,   # Col 1: Valores (nombre, cama)
        ancho_label,  # Col 2: Labels (EDAD, IDENTIFICACIÓN)
        ancho_col3,   # Col 3: Valores (edad, identificación)
        ancho_label,  # Col 4: Labels (ASEGURADORA, FECHA DE INGRESO)
        ancho_col5    # Col 5: Valores (aseguradora, fecha)
    ])
    
    tabla_datos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ('BACKGROUND', (4, 0), (4, -1), colors.lightgrey),
        ('BACKGROUND', (0, 1), (0, 1), colors.lightgrey),
        ('BACKGROUND', (2, 1), (2, 1), colors.lightgrey),
        ('BACKGROUND', (4, 1), (4, 1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),  # Padding reducido
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),  # Padding reducido
        ('TOPPADDING', (0, 0), (-1, -1), 5),  # Padding reducido
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),  # Padding reducido
        ('FONTSIZE', (0, 0), (-1, -1), 6.5),  # Tamaño de fuente reducido
    ]))
    
    story.append(tabla_datos)
    story.append(Spacer(1, 0.3*cm))
    
    # ===== ORGANIZAR MEDICIONES =====
    mediciones_agrupadas = []
    for medicion in mediciones.select_related('formulario').prefetch_related('valores__parametro'):
        fecha_str = medicion.fecha_hora.strftime("%d/%m/%y")
        hora_str = medicion.fecha_hora.strftime("%H:%M")
        
        valores_dict = {}
        for valor_obj in medicion.valores.select_related('parametro').all():
            codigo = valor_obj.parametro.codigo
            valores_dict[codigo] = {
                'valor': valor_obj.valor,
                'puntaje': valor_obj.puntaje if valor_obj.puntaje is not None else 0,
                'parametro': valor_obj.parametro
            }
        
        mediciones_agrupadas.append({
            'fecha': fecha_str,
            'hora': hora_str,
            'medicion': medicion,
            'valores': valores_dict
        })
    
    # ===== GRILLA DE PARÁMETROS =====
    from meows.models import Parametro
    parametros = Parametro.objects.filter(activo=True).order_by('orden')
    
    # ===== CALCULAR ANCHOS DE COLUMNAS PRIMERO (ANTES DE CUALQUIER USO) =====
    # DEFINIR TODAS LAS VARIABLES DE ANCHO PRIMERO - IMPORTANTE: antes de cualquier uso
    ancho_total = landscape(A4)[0] - 1.6*cm  # Menos márgenes
    num_mediciones = max(len(mediciones_agrupadas), 1) if mediciones_agrupadas else 1
    
    # Valores iniciales
    ancho_parametro = 2.9*cm  # Reducido más
    ancho_unidad = 0.8*cm  # Más compacto
    ancho_puntos = 0.85*cm  # Más reducido para evitar que se salga - CRÍTICO: definir siempre primero
    ancho_medicion = 2*cm  # Valor por defecto
    
    # Ancho disponible para las columnas de mediciones
    ancho_disponible = ancho_total - ancho_parametro - ancho_unidad - ancho_puntos
    # Calcular ancho por medición con mínimo de 2cm para que quepa fecha/hora y valores
    if num_mediciones > 0:
        ancho_medicion = ancho_disponible / num_mediciones
    else:
        ancho_medicion = 2*cm
    
    # Asegurar un ancho mínimo de 2cm para cada medición (necesario para fecha/hora/valores)
    if ancho_medicion < 2*cm and num_mediciones > 0:
        ancho_medicion = 2*cm
        # Reajustar otras columnas si es necesario
        ancho_total_necesario = ancho_parametro + ancho_unidad + ancho_puntos + (ancho_medicion * num_mediciones)
        if ancho_total_necesario > ancho_total:
            # Reducir parámetro y unidad si hay muchas mediciones
            ancho_parametro = 2.8*cm
            ancho_unidad = 0.8*cm
            # Recalcular - ancho_puntos ya está definido arriba, no se redefine aquí
            ancho_disponible = ancho_total - ancho_parametro - ancho_unidad - ancho_puntos
            if num_mediciones > 0:
                ancho_medicion = ancho_disponible / num_mediciones
            else:
                ancho_medicion = 2*cm
    
    # Estilo para encabezado de fecha/hora
    estilo_encabezado_fecha = ParagraphStyle(
        'EncabezadoFecha',
        parent=styles['Normal'],
        fontSize=5.5,  # Fuente pequeña para que quepa
        textColor=colors.black,
        alignment=1,  # Centrado
        leading=6.5,  # Espaciado compacto
        spaceAfter=0,
        spaceBefore=0,
    )
    
    # Encabezado de la grilla - FECHA y HORA en encabezados separados por cada medición
    encabezado_grilla = ['PARÁMETRO', 'UNIDAD']
    # Agregar encabezados de fecha y hora para cada medición con formato más compacto
    for item in mediciones_agrupadas:
        # Formato más compacto para evitar desbordamiento
        encabezado_grilla.append(Paragraph(
            f"<b>FECHA</b><br/>{item['fecha']}<br/><b>HORA</b><br/>{item['hora']}",
            estilo_encabezado_fecha
        ))
    encabezado_grilla.append('PUNTOS')
    
    # Datos de la grilla
    datos_grilla = [encabezado_grilla]
    
    # Agregar filas de parámetros
    for parametro in parametros:
        fila = []
        
        # PARÁMETRO
        fila.append(parametro.nombre)
        
        # UNIDAD
        fila.append(parametro.unidad)
        
        # VALORES por medición - Mostrar valor y score
        for item in mediciones_agrupadas:
            valores_hora = item['valores']
            if parametro.codigo in valores_hora:
                valor_data = valores_hora[parametro.codigo]
                valor = str(valor_data['valor'])
                score = valor_data['puntaje']
                # Formato: valor en primera línea, score entre paréntesis en segunda línea
                # Ejemplo: 36.5\n(0) o 39.2\n(3)
                celda_texto = f"{valor}<br/><b>({score})</b>"
                fila.append(Paragraph(celda_texto, estilo_valor_celda))
            else:
                fila.append('')
        
        # PUNTOS (columna de referencia) - Crear sub-tabla con colores
        # Ancho de sub-tabla más pequeño para que quepa dentro de la celda sin desbordarse
        ancho_sub_tabla_puntos = max(ancho_puntos - 0.2*cm, 0.6*cm)  # Reducir más el margen, mínimo 0.6cm
        puntos_tabla = Table([
            ['3'],
            ['2'],
            ['1'],
            ['0']
        ], colWidths=[ancho_sub_tabla_puntos], rowHeights=[0.28*cm, 0.28*cm, 0.28*cm, 0.28*cm])
        
        puntos_tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), obtener_color_score(3)),  # Rojo para 3
            ('BACKGROUND', (0, 1), (0, 1), obtener_color_score(2)),  # Amarillo para 2
            ('BACKGROUND', (0, 2), (0, 2), obtener_color_score(1)),  # Verde para 1
            ('BACKGROUND', (0, 3), (0, 3), obtener_color_score(0)),  # Blanco para 0
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 6),  # Más reducido para que quepa
            ('GRID', (0, 0), (-1, -1), 0.15, colors.black),  # Bordes más delgados
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        fila.append(puntos_tabla)
        
        datos_grilla.append(fila)
    
    # Fila TOTAL - Mostrar total con riesgo/score asociado
    fila_total = ['TOTAL', '']
    for item in mediciones_agrupadas:
        medicion = item['medicion']
        total = medicion.meows_total if medicion.meows_total else 0
        # Determinar el score de riesgo para mostrar junto al total
        riesgo_score = 0
        if medicion.meows_riesgo == "VERDE":
            riesgo_score = 1
        elif medicion.meows_riesgo == "AMARILLO":
            riesgo_score = 2
        elif medicion.meows_riesgo == "ROJO":
            riesgo_score = 3
        # Formato: total en primera línea, score riesgo entre paréntesis en segunda línea
        # Ejemplo: 5\n(2) o 8\n(3) - Formato más compacto
        total_texto = f"<b>{total}</b><br/><b>({riesgo_score})</b>"
        estilo_total = ParagraphStyle(
            'TotalCelda',
            parent=estilo_valor_celda,
            fontSize=6.5,  # Tamaño de fuente reducido
            leading=8,  # Espaciado reducido
        )
        fila_total.append(Paragraph(total_texto, estilo_total))
    # Agregar columna de puntos también en la fila total (puede estar vacía o mostrar referencia)
    # Ancho de sub-tabla más pequeño para que quepa dentro de la celda sin desbordarse
    ancho_sub_tabla_puntos_total = max(ancho_puntos - 0.2*cm, 0.6*cm)  # Reducir más el margen, mínimo 0.6cm
    puntos_tabla_total = Table([
        ['3'],
        ['2'],
        ['1'],
        ['0']
    ], colWidths=[ancho_sub_tabla_puntos_total], rowHeights=[0.28*cm, 0.28*cm, 0.28*cm, 0.28*cm])
    
    puntos_tabla_total.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), obtener_color_score(3)),  # Rojo para 3
        ('BACKGROUND', (0, 1), (0, 1), obtener_color_score(2)),  # Amarillo para 2
        ('BACKGROUND', (0, 2), (0, 2), obtener_color_score(1)),  # Verde para 1
        ('BACKGROUND', (0, 3), (0, 3), obtener_color_score(0)),  # Blanco para 0
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),  # Más reducido para que quepa
        ('GRID', (0, 0), (-1, -1), 0.15, colors.black),  # Bordes más delgados
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    fila_total.append(puntos_tabla_total)
    datos_grilla.append(fila_total)
    
    # Usar los anchos ya calculados anteriormente
    anchos_columnas = [ancho_parametro, ancho_unidad]
    for _ in mediciones_agrupadas:
        anchos_columnas.append(ancho_medicion)
    anchos_columnas.append(ancho_puntos)
    
    # Calcular altura de filas - debe ser suficiente para la sub-tabla de puntos (4 filas)
    altura_fila = 1.2*cm  # Altura ajustada para 4 filas de puntos (0.28cm cada una = 1.12cm + pequeño margen)
    alturas_filas = [0.8*cm]  # Altura del encabezado aumentada para fecha/hora
    # Altura para cada fila de parámetros
    for _ in range(len(parametros)):
        alturas_filas.append(altura_fila)
    # Altura para la fila total
    alturas_filas.append(0.7*cm)  # Altura aumentada para que quepa total y score
    
    # Crear tabla de grilla
    tabla_grilla = Table(datos_grilla, colWidths=anchos_columnas, rowHeights=alturas_filas, repeatRows=1)
    
    # Estilos de la grilla
    estilo_grilla = [
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 6),
        ('FONTSIZE', (0, 1), (-1, -2), 6.5),  # Reducido para evitar desbordamiento
        ('FONTSIZE', (0, -1), (-1, -1), 6.5),  # Fila total reducido
        # Estilo para celdas con valores (columna 2 en adelante, excepto columna de puntos) - Padding reducido
        ('LEFTPADDING', (2, 1), (-2, -2), 2),
        ('RIGHTPADDING', (2, 1), (-2, -2), 2),
        ('TOPPADDING', (2, 1), (-2, -2), 2),
        ('BOTTOMPADDING', (2, 1), (-2, -2), 2),
        # Columna de puntos - padding mínimo para evitar desbordamiento
        ('LEFTPADDING', (-1, 0), (-1, -1), 1),  # Última columna (puntos)
        ('RIGHTPADDING', (-1, 0), (-1, -1), 1),
        ('TOPPADDING', (-1, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (-1, 0), (-1, -1), 1),
        ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),  # Centrar contenido de la columna de puntos
        ('VALIGN', (-1, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        # Columna parámetro
        ('ALIGN', (0, 1), (0, -2), 'LEFT'),  # Columna parámetro alineada a la izquierda
        ('FONTNAME', (0, 1), (0, -2), 'Helvetica-Bold'),  # Parámetros en negrita
        ('BACKGROUND', (0, 1), (0, -2), colors.whitesmoke),  # Fondo gris claro para parámetros
        # Columna unidad
        ('BACKGROUND', (1, 1), (1, -2), colors.whitesmoke),
        # Fila total
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]
    
    # Aplicar colores según scores en las celdas de valores
    fila_idx = 1  # Empezar después del encabezado
    for parametro in parametros:
        col_idx = 2  # Empezar después de PARÁMETRO, UNIDAD
        for item in mediciones_agrupadas:
            valores_hora = item['valores']
            if parametro.codigo in valores_hora:
                valor_data = valores_hora[parametro.codigo]
                score = valor_data['puntaje']
                color = obtener_color_score(score)
                estilo_grilla.append(('BACKGROUND', (col_idx, fila_idx), (col_idx, fila_idx), color))
            col_idx += 1
        fila_idx += 1
    
    # Colorear totales
    fila_total_idx = len(datos_grilla) - 1
    col_idx = 2  # Empezar después de PARÁMETRO, UNIDAD
    for item in mediciones_agrupadas:
        medicion = item['medicion']
        riesgo_color = 0
        if medicion.meows_riesgo == "VERDE":
            riesgo_color = 1
        elif medicion.meows_riesgo == "AMARILLO":
            riesgo_color = 2
        elif medicion.meows_riesgo == "ROJO":
            riesgo_color = 3
        color = obtener_color_score(riesgo_color)
        estilo_grilla.append(('BACKGROUND', (col_idx, fila_total_idx), (col_idx, fila_total_idx), color))
        col_idx += 1
    
    tabla_grilla.setStyle(TableStyle(estilo_grilla))
    
    # Después de aplicar estilos base, reemplazar las celdas de puntos con sub-tablas coloreadas
    # Esto requiere reconstruir la tabla, así que mejor hacemos las celdas de puntos con múltiples estilos
    # Usaremos un enfoque más directo: colorear la celda completa con el color dominante y mostrar los números
    
    # Alternativa: crear filas separadas para cada puntuación (3, 2, 1, 0) en la columna PUNTOS
    # Pero esto complicaría la estructura. Mejor usamos celdas con fondo dividido visualmente
    
    # Vamos a modificar el enfoque: crear la columna de puntos como un string HTML con colores
    # y usar Paragraph para renderizarlo, pero ReportLab no soporta colores en texto simple así
    
    # Solución: crear múltiples estilos de fondo alternados o usar una tabla anidada
    # La mejor opción es dividir visualmente la celda usando colores de fondo segmentados
    
    # Implementación práctica: Colorear toda la columna con un gradiente o dividir en 4 secciones
    # Como ReportLab no permite fácilmente dividir una celda, usaremos una aproximación:
    # Crear 4 celdas pequeñas apiladas verticalmente o usar colores de fondo en franjas
    
    # Mejor solución: Modificar las filas para tener 4 sub-filas en la columna de puntos
    # Pero esto requeriría cambiar toda la estructura de la tabla
    
    # Solución más simple y efectiva: Usar un Table anidado para la columna de puntos
    # o crear la columna de puntos con fondos diferentes por cada número
    story.append(tabla_grilla)
    story.append(Spacer(1, 0.5*cm))
    
    # ===== FIRMA =====
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    hora_actual = datetime.now().strftime("%H:%M")
    responsable = paciente.responsable if paciente.responsable else 'No especificado'
    
    # Estilo profesional para la firma
    estilo_firma = ParagraphStyle(
        'Firma',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        alignment=0,  # Izquierda
        leading=12,
        spaceAfter=0,
        spaceBefore=0,
        fontName='Helvetica-Bold',
    )
    
    # Crear texto con formato más profesional y espaciado
    firma_texto = (
        f'<b>Enfermero(a):</b> {responsable}  '
        f'<b>Fecha:</b> {fecha_actual}  '
        f'<b>Hora:</b> {hora_actual}'
    )
    
    firma_data = [
        [Paragraph(firma_texto, estilo_firma)]
    ]
    
    # Calcular ancho total disponible
    ancho_total_firma = landscape(A4)[0] - 1.6*cm
    
    tabla_firma = Table(firma_data, colWidths=[ancho_total_firma])
    tabla_firma.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0066CC')),  # Azul profesional
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Totalmente a la izquierda
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),  # Texto blanco para contraste
        ('LEFTPADDING', (0, 0), (-1, -1), 12),  # Padding izquierdo generoso
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),  # Padding vertical aumentado
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#0052A3')),  # Borde azul más oscuro
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#0052A3')),  # Borde completo
    ]))
    
    story.append(Spacer(1, 0.3*cm))  # Espacio antes de la firma
    story.append(tabla_firma)
    
    # Construir PDF
    doc.build(story)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    nombre_archivo = f"MEOWS_{paciente.numero_documento}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    return response
