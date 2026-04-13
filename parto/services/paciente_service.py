from django.db.models import Q
from parto.models import Paciente 
from meows.models import (
    Genpacien, Adningreso, Hpnestanc, Hpndefcam, 
    Hcnfolio, Hcndiapac, Gendetcon, Gendiagno
)

def obtener_info_ingreso_activo(documento):
    """
    Busca si el paciente con el documento dado tiene un ingreso activo.
    Retorna un diccionario con detalles amplios para poblar el formulario,
    incluyendo DIAGNOSTICO y ASEGURADORA.
    """
    try:
        # 1. Buscar paciente en GENPACIEN (Base readonly)
        paciente_ext = Genpacien.objects.using('readonly').filter(PACNUMDOC=documento).first()
        if not paciente_ext:
            return None

        # 2. Buscar último ingreso ACTIVO (AINESTADO=0)
        ingreso_activo = Adningreso.objects.using('readonly').filter(
            GENPACIEN=paciente_ext,
            AINESTADO=0 
        ).order_by('-OID').first()

        cama_nombre = None
        aseguradora_nombre = None
        diagnostico_texto = "SIN DIAGNÓSTICO"
        fecha_ingreso = None
        ingreso_id = None

        if ingreso_activo:
            ingreso_id = ingreso_activo.AINCONSEC
            fecha_ingreso = ingreso_activo.AINFECING

            # 3. Buscar estancia activa
            estancia_activa = Hpnestanc.objects.using('readonly').filter(
                ADNINGRES=ingreso_activo,
                HESFECSAL__isnull=True
            ).select_related('HPNDEFCAM').order_by('-OID').first()

            if estancia_activa and estancia_activa.HPNDEFCAM:
                nombre_cama = estancia_activa.HPNDEFCAM.HCANOMBRE
                habitacion = estancia_activa.HPNDEFCAM.HCANUMHABI
                if habitacion and habitacion.strip():
                    cama_nombre = f"{habitacion} - {nombre_cama}"
                else:
                    cama_nombre = nombre_cama
            
            # 4. Obtener Aseguradora (GENDETCON)
            if ingreso_activo.GENDETCON_id:
                try:
                    det_con = Gendetcon.objects.using('readonly').filter(OID=ingreso_activo.GENDETCON_id).first()
                    if det_con:
                        aseguradora_nombre = det_con.GDENOMBRE
                except Exception:
                    pass
            
            # 5. Obtener Diagnóstico (HCNFOLIO -> HCNDIAPAC -> GENDIAGNO)
            try:
                # Buscar último folio del ingreso
                ultimo_folio = Hcnfolio.objects.using('readonly').filter(
                    ADNINGRESO=ingreso_activo
                ).order_by('-HCNUMFOL').first()

                if ultimo_folio:
                    # Buscar diagnósticos de este folio
                    diag_pac = Hcndiapac.objects.using('readonly').filter(
                        HCNFOLIO=ultimo_folio
                    ).select_related('GENDIAGNO').first()

                    if diag_pac and diag_pac.GENDIAGNO:
                        diagnostico_texto = f"{diag_pac.GENDIAGNO.DIACODIGO} - {diag_pac.GENDIAGNO.DIANOMBRE}"
            except Exception as e:
                print(f"Error recuperando diagnóstico: {e}")

        # Construir nombre completo
        nombres = f"{paciente_ext.PACPRINOM or ''} {paciente_ext.PACSEGNOM or ''}".strip()
        apellidos = f"{paciente_ext.PACPRIAPE or ''} {paciente_ext.PACSEGAPE or ''}".strip()
        
        # Fecha nacimiento
        fecha_nacimiento = None
        if paciente_ext.GPAFECNAC:
            fecha_nacimiento = paciente_ext.GPAFECNAC.date() if hasattr(paciente_ext.GPAFECNAC, 'date') else paciente_ext.GPAFECNAC
            
        # Calcular edad
        edad_anios = None
        from datetime import date
        if fecha_nacimiento:
            hoy = date.today()
            edad_anios = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

        resultado = {
            'es_activo': ingreso_activo is not None,
            'ingreso_id': ingreso_id,
            'fecha_ingreso': fecha_ingreso,
            'cama': cama_nombre,
            'aseguradora': aseguradora_nombre,
            'diagnostico': diagnostico_texto,
            'num_identificacion': paciente_ext.PACNUMDOC,
            'tipo_identificacion': paciente_ext.PACTIPDOC,
            'nombres_raw': nombres,
            'apellidos_raw': apellidos,
            'nombre_completo': f"{nombres} {apellidos}".strip(),
            'fecha_nacimiento': fecha_nacimiento,
            'edad': edad_anios,
            'num_historia_clinica': paciente_ext.PACNUMDOC, # Fallback a documento si no hay campo separado
            'sexo': paciente_ext.GPASEXPAC,
            'tipo_sangre': None,
        }
        
        # Intentar completar datos con información local (ej. Tipo de Sangre)
        try:
            paciente_local = Paciente.objects.filter(num_identificacion=paciente_ext.PACNUMDOC).first()
            if paciente_local:
                if not resultado['tipo_sangre']:
                    resultado['tipo_sangre'] = paciente_local.tipo_sangre
        except Exception:
            pass
            
        return resultado

    except Exception as e:
        print(f"Error obteniendo info ingreso activo: {e}")
        return None

def buscar_pacientes_activos_gineco_filtro(query):
    """
    Busca pacientes activos filtrando especificamente por áreas de GINECO u OBSTETRICIA
    en la tabla HPNDEFCAM.
    """
    resultados = []
    try:
        # Filtros de áreas por NOMBRE, coincidiendo con la logica que pide el usuario
        filtros_area = Q(HPNDEFCAM__HCANOMBRE__icontains='GINECO') | \
                       Q(HPNDEFCAM__HCANOMBRE__icontains='OBSTETRICIA') | \
                       Q(HPNDEFCAM__HCANOMBRE__icontains='PARTOS')

        if not query:
            # Traer los últimos 30 pacientes en estas áreas (GINECO/OBSTETRICIA)
            estancias = Hpnestanc.objects.using('readonly').filter(
                HESFECSAL__isnull=True  # Estancia abierta (activa)
            ).filter(filtros_area).select_related(
                'ADNINGRES', 'ADNINGRES__GENPACIEN', 'HPNDEFCAM'
            ).order_by('-OID')[:30]
            
            for est in estancias:
                try:
                    ing = est.ADNINGRES
                    pac = ing.GENPACIEN
                    # Solo mostrar si tiene ingreso activo (AINESTADO=0)
                    if ing.AINESTADO == 0: 
                        nombre_cama = est.HPNDEFCAM.HCANOMBRE
                        habitacion = est.HPNDEFCAM.HCANUMHABI
                        cama_str = f"{habitacion} - {nombre_cama}" if (habitacion and habitacion.strip()) else nombre_cama
                        
                        resultados.append({
                            'documento': pac.PACNUMDOC,
                            'nombre_completo': f"{pac.PACPRINOM} {pac.PACSEGNOM or ''} {pac.PACPRIAPE} {pac.PACSEGAPE or ''}".strip(),
                            'ingreso': ing.AINCONSEC,
                            'fecha': ing.AINFECING,
                            'cama': cama_str
                        })
                except Exception:
                    continue
        else:
            # Búsqueda por documento o nombre
            q_filtro = Q(PACNUMDOC__icontains=query) | \
                       Q(PACPRINOM__icontains=query) | \
                       Q(PACPRIAPE__icontains=query)
                       
            pacientes_matches = Genpacien.objects.using('readonly').filter(q_filtro)[:50]
            ids_pacientes = [p.OID for p in pacientes_matches]
            
            if ids_pacientes:
                # Buscar estancias activas de estos pacientes EN LAS AREAS REQUERIDAS
                estancias = Hpnestanc.objects.using('readonly').filter(
                    ADNINGRES__GENPACIEN__in=ids_pacientes,
                    HESFECSAL__isnull=True
                ).filter(filtros_area).select_related(
                    'ADNINGRES', 'ADNINGRES__GENPACIEN', 'HPNDEFCAM'
                ).order_by('-OID')
                
                for est in estancias:
                    try:
                        ing = est.ADNINGRES
                        pac = ing.GENPACIEN
                        if ing.AINESTADO == 0:
                            nombre_cama = est.HPNDEFCAM.HCANOMBRE
                            habitacion = est.HPNDEFCAM.HCANUMHABI
                            cama_str = f"{habitacion} - {nombre_cama}" if (habitacion and habitacion.strip()) else nombre_cama
                            
                            resultados.append({
                                'documento': pac.PACNUMDOC,
                                'nombre_completo': f"{pac.PACPRINOM} {pac.PACSEGNOM or ''} {pac.PACPRIAPE} {pac.PACSEGAPE or ''}".strip(),
                                'ingreso': ing.AINCONSEC,
                                'fecha': ing.AINFECING,
                                'cama': cama_str
                            })
                    except Exception:
                        continue

    except Exception as e:
        print(f"Error buscando pacientes gineco: {e}")
        
    return resultados
