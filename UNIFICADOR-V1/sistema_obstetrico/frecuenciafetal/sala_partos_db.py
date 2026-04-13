"""
Consulta a DGEMPRES03 (readonly) - Sala de Partos / MEOWS.
Solo lectura. Usado para arrastrar datos de paciente al formulario FRSPA-007.
"""
from django.db import connections
from django.conf import settings


def _normalizar_edad_gestacional(val):
    """Convierte valor de edad gestacional a semanas (preservando decimales si existen)."""
    if val is None:
        return None
    try:
        f = float(str(val).replace(',', '.').split()[0])
        # Si es un número entero (ej: 38.0), devolver como int
        if f == int(f):
            return int(f)
        return round(f, 1) # Preservar un decimal (ej: 38.5)
    except (ValueError, IndexError, TypeError):
        return None


def _normalizar_gestas(val):
    """Convierte G (gestas) a entero."""
    if val is None:
        return 1
    try:
        n = int(round(float(val)))
        return max(1, n) if n >= 1 else 1
    except (ValueError, TypeError):
        return 1


def listar_pacientes_sala_partos(query=None):
    """
    Ejecuta la consulta de Control de Trabajo de Parto / MEOWS contra
    la BD readonly (DGEMPRES03) y devuelve lista de dicts listos para
    el formulario FRSPA-007.

    query: opcional; filtra por nombre o identificación (documento).
    """
    if 'readonly' not in settings.DATABASES:
        return []

    sql = """
    SELECT 
        EST.HESFECING AS fecha_ingreso,
        PLA.GDENOMBRE AS aseguradora,
        PAC.GPANUMCAR AS historia_clinica,
        PAC.PACNUMDOC AS identificacion,
        RTRIM(ISNULL(PAC.PACPRINOM,'') + ' ' + ISNULL(PAC.PACSEGNOM,'') + ' ' + ISNULL(PAC.PACPRIAPE,'') + ' ' + ISNULL(PAC.PACSEGAPE,'')) AS nombre_paciente,
        FOL_DATA.diagnostico,
        DATEDIFF(YEAR, PAC.GPAFECNAC, GETDATE()) AS edad_anos,
        FOL_DATA.grupo_sanguineo,
        FOL_DATA.edad_gestacional_raw,
        FOL_DATA.G_gestas,
        FOL_DATA.P,
        FOL_DATA.C,
        FOL_DATA.A,
        FOL_DATA.controles_prenatales,
        ING.AINCONSEC AS numero_ingreso,
        CAM.HCACODIGO AS numero_cama
    FROM HPNESTANC AS EST
    INNER JOIN HPNDEFCAM AS CAM ON EST.HPNDEFCAM = CAM.OID
    INNER JOIN HPNGRUPOS AS GRP ON CAM.HPNGRUPOS = GRP.OID
    INNER JOIN HPNSUBGRU AS SUB ON CAM.HPNSUBGRU = SUB.OID
    INNER JOIN ADNINGRESO AS ING ON EST.ADNINGRES = ING.OID
    INNER JOIN GENPACIEN AS PAC ON ING.GENPACIEN = PAC.OID
    INNER JOIN GENDETCON AS PLA ON ING.GENDETCON = PLA.OID
    OUTER APPLY (
        SELECT TOP 1 
            (SELECT TOP 1 DX.DIACODIGO + ' ' + DX.DIANOMBRE 
             FROM HCNDIAPAC AS DIAP 
             INNER JOIN GENDIAGNO AS DX ON DIAP.GENDIAGNO = DX.OID 
             WHERE DIAP.HCNFOLIO = FOL.OID 
             ORDER BY DIAP.OID ASC) AS diagnostico,
            MW.HCCM03N191 AS grupo_sanguineo,
            MW.HCCM00N256 AS edad_gestacional_raw,
            MW.HCCM01N318 AS G_gestas,
            MW.HCCM01N319 AS P,
            MW.HCCM01N320 AS C,
            MW.HCCM01N321 AS A,
            MW.HCCM00N255 AS controles_prenatales
        FROM HCNFOLIO AS FOL
        LEFT OUTER JOIN HCMWINGIN AS MW ON FOL.OID = MW.HCNFOLIO
        WHERE FOL.ADNINGRESO = ING.OID
        ORDER BY FOL.OID DESC
    ) AS FOL_DATA
    WHERE EST.HESFECSAL IS NULL
      AND GRP.HGRCODIGO = '03'
      AND SUB.HSUCODIGO = '0305'
    """
    params = []
    if query and query.strip():
        sql += """
      AND (
          PAC.PACNUMDOC LIKE %s
          OR PAC.PACPRINOM + ' ' + ISNULL(PAC.PACSEGNOM,'') + ' ' + PAC.PACPRIAPE + ' ' + ISNULL(PAC.PACSEGAPE,'') LIKE %s
          OR PAC.PACPRIAPE + ' ' + ISNULL(PAC.PACSEGAPE,'') LIKE %s
      )
        """
        q = '%' + query.strip() + '%'
        params = [q, q, q]

    sql += " ORDER BY CAM.HCACODIGO"

    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        raise RuntimeError(f'Error al consultar DGEMPRES03: {e}') from e

    # Mapear a formato esperado por el formulario
    out = []
    for r in rows:
        nombre = (r.get('nombre_paciente') or '').strip()
        ident = (r.get('identificacion') or '').strip()
        eg_raw = r.get('edad_gestacional_raw')
        gestas_raw = r.get('G_gestas')

        out.append({
            'nombre_paciente': nombre or None,
            'identificacion': ident or None,
            'edad_gestacional': _normalizar_edad_gestacional(eg_raw),
            'gestas': _normalizar_gestas(gestas_raw),
            'nombre_acompanante': None,
            'numero_cama': r.get('numero_cama'),
            'numero_ingreso': r.get('numero_ingreso'),
            'historia_clinica': r.get('historia_clinica'),
            'aseguradora': r.get('aseguradora'),
            'diagnostico': r.get('diagnostico'),
            'edad_anos': r.get('edad_anos'),
            'fecha_ingreso': r.get('fecha_ingreso'),
            'grupo_sanguineo': r.get('grupo_sanguineo'),
            'controles_prenatales': r.get('controles_prenatales'),
            'origen': 'sala_partos',
        })
    return out[:50]
