"""
Generador de PDF para el formato FRSPA-007 - Control Fetocardia y Postparto
Estructura ordenada tipo plantilla hospitalaria.
"""
import io
import base64
import os
from reportlab.lib import colors, utils
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from .models import (
    ControlPostpartoInmediato, HuellaBebe, FirmaPaciente, Huella
)
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image
)
from reportlab.lib.enums import TA_CENTER
from django.conf import settings

# Dimensiones A4: 21 x 29.7 cm. Márgenes 0.9cm = 19.2 x 27.9 cm útil (ocupa toda la hoja)
MARGIN = 0.9 * cm
ANCHO_UTIL = 19.2 * cm
BORDE = 0.8
COLOR_BORDE = colors.HexColor('#475569')
COLOR_HEADER = colors.HexColor('#0e7490')
COLOR_LABEL = colors.HexColor('#f1f5f9')
COLOR_TEXTO = colors.HexColor('#1e293b')


def _get_logo_path(filename):
    return settings.BASE_DIR / 'media' / 'img' / filename


def _safe_str(val):
    if val is None:
        return ''
    if hasattr(val, 'strftime'):
        return str(val)
    return str(val)


def _fix_mojibake_text(value):
    text = _safe_str(value)
    if not text:
        return ''
    # Corrige casos típicos: "MarÝa", "Gonzßlez", "JosÃ©", etc.
    if not any(ch in text for ch in ('Ã', 'Â', 'Ä', 'Ë', 'Ï', 'Ö', 'Ü', 'Ý', 'ß')):
        return text
    for src_enc in ('latin-1', 'cp1252'):
        try:
            repaired = text.encode(src_enc, errors='strict').decode('utf-8', errors='strict')
            if repaired:
                return repaired
        except Exception:
            continue
    return text


# Dimensiones fijas de la huella: tamaño considerable sin desbordar la card (ancho col 9.0 cm)
HUELLA_ANCHO_CM = 8.7
HUELLA_ALTO_CM = 9.5


def _huella_image_fit(img_source):
    """
    Crea una imagen ReportLab con tamaño predeterminado fijo.
    Siempre se escala para ocupar el máximo espacio de la card de huella.
    """
    try:
        if hasattr(img_source, 'seek'):
            img_source.seek(0)
        w = HUELLA_ANCHO_CM * cm
        h = HUELLA_ALTO_CM * cm
        img = Image(img_source, width=w, height=h, kind='proportional')
        img._restrictSize(w, h)
        return img
    except Exception:
        return None


def _huella_image_from_rn(control_rn):
    """Obtiene la imagen de huella desde base64 o archivo, adaptada al recuadro."""
    if control_rn.huella_pie_base64:
        try:
            b64 = control_rn.huella_pie_base64
            if ',' in b64:
                b64 = b64.split(',')[1]
            img_bytes = io.BytesIO(base64.b64decode(b64))
            return _huella_image_fit(img_bytes)
        except Exception:
            pass
    if control_rn.huella_pie:
        try:
            # 1. Intentar por path si existe
            if os.path.exists(control_rn.huella_pie.path):
                return _huella_image_fit(control_rn.huella_pie.path)
            else:
                # 2. Fallback memoria
                control_rn.huella_pie.open('rb')
                img_bytes = io.BytesIO(control_rn.huella_pie.read())
                control_rn.huella_pie.close()
                return _huella_image_fit(img_bytes)
        except Exception as e_rn:
            print(f"Error cargando huella RN: {e_rn}")
            pass
    return None


def generar_pdf_registro(registro):
    """Genera PDF FRSPA-007 con estructura ordenada."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )
    elements = []
    styles = getSampleStyleSheet()

    # ========== ENCABEZADO ==========
    logo_h = _get_logo_path('logo_hospital.png')
    logo_a = _get_logo_path('logo_acreditacion.png')
    try:
        c1 = Image(str(logo_h), width=2.2*cm, height=1.6*cm) if logo_h.exists() else Paragraph('', styles['Normal'])
    except Exception:
        c1 = Paragraph('', styles['Normal'])
    c2 = Paragraph(
        '<b>HOSPITAL UNIVERSITARIO DEPARTAMENTAL DE NARIÑO</b><br/>'
        '<font size="8">SALA RECIÉN NACIDOS</font><br/>'
        '<font size="6">Control Fetocardia Expulsivo · Posparto Inmediato · Recién Nacido — FRSPA-007 V01</font>',
        ParagraphStyle(name='HeaderCenter', alignment=TA_CENTER, fontSize=10, spaceAfter=2)
    )
    try:
        c3 = Image(str(logo_a), width=2.2*cm, height=1.6*cm) if logo_a.exists() else Paragraph('', styles['Normal'])
    except Exception:
        c3 = Paragraph('', styles['Normal'])
    tbl_head = Table([[c1, c2, c3]], colWidths=[2.8*cm, 13.6*cm, 2.8*cm])
    tbl_head.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
    ]))
    elements.append(tbl_head)
    elements.append(Spacer(1, 0.5*cm))

    # ========== DATOS DE LA PACIENTE ==========
    data_pac = [
        ['Nombre completo:', _safe_str(registro.nombre_paciente), 'N° Identificación:', _safe_str(registro.identificacion)],
        ['Edad Gestacional:', f"{registro.edad_gestacional} sem" if registro.edad_gestacional else '—', 'Gestas:', _safe_str(registro.gestas)],
        ['Acompañante:', _safe_str(registro.nombre_acompanante) or '—', '', ''],
    ]
    tbl_pac = Table([['DATOS DE LA PACIENTE', '', '', '']] + data_pac, colWidths=[4.5*cm, 5.1*cm, 4.5*cm, 5.1*cm])
    tbl_pac.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (0, -1), COLOR_LABEL),
        ('BACKGROUND', (2, 1), (2, -1), COLOR_LABEL),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(tbl_pac)
    elements.append(Spacer(1, 0.45*cm))

    # ========== CARACTERÍSTICAS DEL PARTO ==========
    tipo_p = dict(registro.PARTO_CHOICES).get(registro.tipo_parto, registro.tipo_parto or '—')
    tipo_a = dict(registro.ALUMBRAMIENTO_CHOICES).get(registro.tipo_alumbramiento, registro.tipo_alumbramiento or '—')
    data_part = [
        ['Tipo parto:', tipo_p, 'Episiotomía:', 'Sí' if registro.episiotomia else 'No'],
        ['Alumbramiento:', tipo_a, 'Atendido por:', _safe_str(registro.parto_atendido_por) or '—'],
    ]
    tbl_part = Table([['CARACTERÍSTICAS DEL PARTO', '', '', '']] + data_part, colWidths=[4.5*cm, 5.1*cm, 4.5*cm, 5.1*cm])
    tbl_part.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (0, -1), COLOR_LABEL),
        ('BACKGROUND', (2, 1), (2, -1), COLOR_LABEL),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(tbl_part)
    elements.append(Spacer(1, 0.45*cm))

    # ========== CONTROL FETOCARDIA ==========
    fcs = registro.controles_fetocardia.all().order_by('fecha', 'hora')
    data_fc = [['#', 'Fecha', 'Hora', 'Fetocardia (lpm)', 'Responsable']]
    for i, fc in enumerate(fcs, 1):
        data_fc.append([str(i), _safe_str(fc.fecha), _safe_str(fc.hora), str(fc.fetocardia), _safe_str(fc.responsable)])
    if not data_fc[1:]:
        data_fc.append(['Sin registros', '', '', '', ''])
    fila_tit_fc = ['CONTROL DE FETOCARDIA DURANTE EL EXPULSIVO'] + ['']*4
    tbl_fc = Table([fila_tit_fc] + data_fc, colWidths=[1.2*cm, 3.2*cm, 2.2*cm, 3.2*cm, 9.4*cm])
    tbl_fc.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#0c4a6e')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(tbl_fc)
    elements.append(Spacer(1, 0.45*cm))

    # ========== RECIÉN NACIDO + HUELLA (dos columnas) ==========
    try:
        rn = registro.control_recien_nacido
    except Exception:
        rn = None

    if rn:
        gen = dict(rn.GENERO_CHOICES).get(rn.genero, rn.genero)
        data_rn = [
            ['Hora nacimiento:', _safe_str(rn.hora_nacimiento), 'UCI:', 'Sí' if rn.pasa_uci_neonatal else 'No', 'Causa UCI:', _safe_str(rn.causa_uci) or '—'],
            ['Género:', gen, 'Peso (g):', str(rn.peso), 'Talla (cm):', str(rn.talla)],
            ['PC:', _safe_str(rn.pc) or '—', 'PT:', _safe_str(rn.pt) or '—', 'P.Abd:', _safe_str(rn.p_abd) or '—'],
            ['APGAR 1 min:', str(rn.apgar_1min), 'APGAR 5 min:', str(rn.apgar_5min), 'APGAR 10 min:', _safe_str(rn.apgar_10min) or '—'],
            ['TSH:', _safe_str(rn.tsh) or '—', 'Hemoclasif.:', _safe_str(rn.hemoclasificacion) or '—', 'Vacunas:', ('Sí' if rn.vacuna_hb else 'No') + '/' + ('Sí' if rn.vacuna_bcg else 'No')],
            ['Líquido amniótico:', _safe_str(rn.caracteristicas_liquido_amniotico) or '—', '', '', '', ''],
            ['Lavado gástrico:', 'Sí' if rn.lavado_gastrico else 'No', 'Elimina:', 'Sí' if rn.lavado_elimina else 'No', 'Meconio:', 'Sí' if rn.meconio else 'No'],
        ]
        # Tabla RN: 6 cols, suma 10.2cm (ancho col izq)
        cw_rn = [1.75*cm, 1.65*cm, 1.75*cm, 1.65*cm, 1.75*cm, 1.65*cm]
        tbl_rn = Table(data_rn, colWidths=cw_rn)
        tbl_rn.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), COLOR_LABEL),
            ('BACKGROUND', (2, 0), (2, -1), COLOR_LABEL),
            ('BACKGROUND', (4, 0), (4, -1), COLOR_LABEL),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (4, 0), (4, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))

        # Glucometrías
        glucs = rn.glucometrias.all().order_by('hora')
        tbl_gluc = None
        if glucs.exists():
            data_gluc = [['Hora', 'Resultado (mg/dL)']]
            for g in glucs:
                data_gluc.append([_safe_str(g.hora), str(g.resultado)])
            tbl_gluc = Table(data_gluc, colWidths=[2.5*cm, 3*cm])
            tbl_gluc.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ]))

        # Huella
        img_huella = _huella_image_from_rn(rn)

        # Col izq — col der para huella = 19.2cm total
        ancho_izq = 10.2 * cm
        ancho_der = 9.0 * cm
        tit_rn = Table([['DATOS DEL RECIÉN NACIDO']], colWidths=[ancho_izq])
        tit_rn.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
        ]))
        tit_h = Table([['HUELLA DEL PIE']], colWidths=[ancho_der])
        tit_h.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
        ]))
        if img_huella:
            tbl_h = Table([[img_huella]], colWidths=[ancho_der])
            tbl_h.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 28),
            ]))
        else:
            tbl_h = Table([['—']], colWidths=[ancho_der])
            tbl_h.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 28),
                ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
            ]))
        col_izq = [tit_rn, tbl_rn]
        if tbl_gluc:
            col_izq.append(Spacer(1, 0.1*cm))
            col_izq.append(Paragraph('<b>Glucometrías</b>', ParagraphStyle(name='Gluc', fontSize=8, spaceAfter=2)))
            col_izq.append(tbl_gluc)
        col_der = [tit_h, tbl_h]
        tbl_rn_huella = Table([[col_izq, col_der]], colWidths=[ancho_izq, ancho_der])
        tbl_rn_huella.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, -1), 3),
            ('LEFTPADDING', (1, 0), (1, -1), 3),
            ('RIGHTPADDING', (1, 0), (1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
            ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
        ]))
        elements.append(tbl_rn_huella)
    else:
        empty_rn = Table([['DATOS DEL RECIÉN NACIDO'], ['Sin datos de recién nacido']], colWidths=[ANCHO_UTIL])
        empty_rn.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(empty_rn)

    elements.append(Spacer(1, 0.45*cm))

    # ========== CONTROL POSTPARTO ==========
    pps = registro.controles_postparto.all().order_by('fecha', 'hora')
    data_pp = [['Min', 'Fecha', 'Hora', 'T/A', 'Temp', 'Pulso', 'Resp', 'Involución', 'Responsable']]
    for pp in pps:
        data_pp.append([
            str(pp.minuto_control), _safe_str(pp.fecha), _safe_str(pp.hora),
            _safe_str(pp.tension_arterial) or '—', _safe_str(pp.temperatura) or '—',
            _safe_str(pp.pulso) or '—', _safe_str(pp.respiracion) or '—',
            _safe_str(pp.involucion_uterina) or '—',
            _safe_str(pp.responsable) or '—'
        ])
    if not data_pp[1:]:
        data_pp.append(['Sin registros'] + ['']*8)
    # 9 columnas — ancho total ANCHO_UTIL (19.2 cm)
    cw_pp = [1.45*cm]*8 + [6.15*cm]
    fila_titulo = ['CONTROL POSTPARTO INMEDIATO'] + ['']*8
    tbl_pp = Table([fila_titulo] + data_pp, colWidths=cw_pp)
    tbl_pp.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#0c4a6e')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('BOX', (0, 0), (-1, -1), BORDE, COLOR_BORDE),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(tbl_pp)

    # ========== FIRMA PACIENTE + BIOMETRÍA ==========
    if registro.firma_paciente or FirmaPaciente.objects.filter(paciente_id=registro.identificacion.replace('.', '').replace('-', '')).exists():
        elements.append(Spacer(1, 0.5*cm))
        
        # Firma Manuscrita
        img_manuscrita = None
        if registro.firma_paciente:
            try:
                # 1. Intentar por path físico si existe
                if os.path.exists(registro.firma_paciente.path):
                    img_manuscrita = Image(registro.firma_paciente.path, width=5.0*cm, height=2.0*cm, kind='proportional')
                else:
                    # 2. Fallback memoria
                    registro.firma_paciente.open('rb')
                    img_bytes = io.BytesIO(registro.firma_paciente.read())
                    registro.firma_paciente.close()
                    img_manuscrita = Image(img_bytes, width=5.0*cm, height=2.0*cm, kind='proportional')
            except Exception as e_sig:
                print(f"Error cargando firma manuscrita Fetal: {e_sig}")
                img_manuscrita = None

        # Huella Biométrica
        img_biometrica = None
        id_numerica = registro.identificacion.replace('.', '').replace('-', '')
        
        # 1. Buscar en FirmaPaciente vinculada al formulario
        huella_obj = FirmaPaciente.objects.filter(formulario=registro).order_by('-fecha').first()
        
        # 2. Si no hay, buscar en FirmaPaciente por ID de paciente
        if not huella_obj:
            huella_obj = FirmaPaciente.objects.filter(paciente_id=id_numerica).order_by('-fecha').first()
            
        if huella_obj and huella_obj.imagen_huella:
            try:
                # Intentar por path físico si existe
                if os.path.exists(huella_obj.imagen_huella.path):
                    img_biometrica = Image(huella_obj.imagen_huella.path, width=2.5*cm, height=3.0*cm, kind='proportional')
                else:
                    # Fallback memoria
                    huella_obj.imagen_huella.open('rb')
                    img_bytes = io.BytesIO(huella_obj.imagen_huella.read())
                    huella_obj.imagen_huella.close()
                    img_biometrica = Image(img_bytes, width=2.5*cm, height=3.0*cm, kind='proportional')
            except Exception as e_huella:
                print(f"Error cargando huella biométrica Fetal: {e_huella}")
                img_biometrica = None
        
        # 3. Si aún no hay, buscar en el modelo Huella (capturas directas Android)
        if not img_biometrica:
            huella_raw = Huella.objects.filter(documento=registro.identificacion).order_by('-fecha').first()
            if not huella_raw:
                # Reintentar con ID numérica por si acaso
                huella_raw = Huella.objects.filter(documento=id_numerica).order_by('-fecha').first()
                
            if huella_raw and huella_raw.imagen_huella:
                try:
                    try:
                        huella_path = huella_raw.imagen_huella.path
                        img_biometrica = Image(huella_path, width=2.5*cm, height=3.0*cm, kind='proportional')
                    except Exception:
                        huella_raw.imagen_huella.open('rb')
                        img_bytes = io.BytesIO(huella_raw.imagen_huella.read())
                        huella_raw.imagen_huella.close()
                        img_biometrica = Image(img_bytes, width=2.5*cm, height=3.0*cm, kind='proportional')
                except Exception:
                    pass

        fecha_firma = registro.fecha_hora_firma.strftime('%d/%m/%Y %H:%M') if registro.fecha_hora_firma else (huella_obj.fecha.strftime('%d/%m/%Y %H:%M') if huella_obj else '—')
        
        # Organizar en tabla
        col_firma = []
        if img_manuscrita:
            col_firma.append(img_manuscrita)
        sig_name = (_fix_mojibake_text(registro.nombre_firma_paciente) or "").strip()
        prof_name = (_fix_mojibake_text(registro.profesional_nombre) or "").strip()
        final_name = sig_name or prof_name or "—"

        col_firma.append(Paragraph(f"<b>{final_name}</b>", styles['Normal']))
        col_firma.append(Paragraph(f"<font size='7' color='#64748b'>FIRMA DEL RESPONSABLE — {fecha_firma}</font>", styles['Normal']))

        col_biometria = []
        if img_biometrica:
            col_biometria.append(img_biometrica)
            col_biometria.append(Paragraph("<font size='7' color='#64748b'>HUELLA BIOMÉTRICA</font>", ParagraphStyle(name='CenterGray', parent=styles['Normal'], alignment=TA_CENTER)))

        data_firmas = [[col_firma, col_biometria]]
        tbl_firmas = Table(data_firmas, colWidths=[13.2*cm, 6.0*cm])
        tbl_firmas.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LINEABOVE', (0, 0), (0, 0), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(tbl_firmas)

    # ========== FIRMA PROFESIONAL (DGH) ==========
    if registro.firma_profesional_base64:
        elements.append(Spacer(1, 0.5*cm))
        try:
            b64 = registro.firma_profesional_base64
            if ',' in b64:
                b64 = b64.split(',')[1]
            img_bytes = io.BytesIO(base64.b64decode(b64))
            img_prof = Image(img_bytes, width=5.0*cm, height=2.0*cm, kind='proportional')
            
            # Bloque de Validación similar a MEOWS
            elements.append(Spacer(1, 0.4*cm))
            valid_estilo = ParagraphStyle('ValidProf', parent=styles['Normal'], fontSize=8.5, fontName='Helvetica-Bold')
            valid_texto = (
                f"<b>VALIDACIÓN DE DILIGENCIAMIENTO (PROFESIONAL RESPONSABLE)</b><br/>"
                f"Responsable: {registro.profesional_nombre or '—'} | ID: {registro.profesional_identificacion or '—'} | T.P.: {registro.profesional_tarjeta_pro or '—'}<br/>"
                f"Fecha de Registro: {registro.created_at.strftime('%d/%m/%Y %H:%M')}"
            )
            
            data_prof = [
                [img_prof, ''],
                [Paragraph(valid_texto, valid_estilo), '']
            ]
            tbl_prof = Table(data_prof, colWidths=[6.0*cm, 13.2*cm])
            tbl_prof.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(tbl_prof)
        except Exception as e:
            elements.append(Paragraph(f"<font size='7' color='red'>Error al cargar firma profesional: {str(e)}</font>", styles['Normal']))

    doc.build(elements)
    return buffer.getvalue()
