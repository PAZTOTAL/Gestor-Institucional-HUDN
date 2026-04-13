from django.db.models import Q
from meows.models import Genpacien, Adningreso, Hpnestanc, Paciente

def obtener_info_ingreso_activo(documento):
    """
    Busca si el paciente con el documento dado tiene un ingreso activo.
    Retorna un diccionario con detalles (cama, aseguradora, etc.) o None.
    """
    try:
        # 1. Buscar paciente en GENPACIEN
        paciente_ext = Genpacien.objects.using('readonly').filter(PACNUMDOC=documento).first()
        if not paciente_ext:
            return None

        # 2. Buscar último ingreso ACTIVO (AINESTADO=0)
        # Nota: AINESTADO=0 suele ser 'Activo' o 'Abierto'.
        ingreso_activo = Adningreso.objects.using('readonly').filter(
            GENPACIEN=paciente_ext,
            AINESTADO=0 
        ).order_by('-OID').first()

        if not ingreso_activo:
            return None

        # 3. Buscar estancia activa (HESFECSAL es NULL) asociada a este ingreso
        estancia_activa = Hpnestanc.objects.using('readonly').filter(
            ADNINGRES=ingreso_activo,
            HESFECSAL__isnull=True
        ).select_related('HPNDEFCAM').order_by('-OID').first()

        cama_nombre = None
        if estancia_activa and estancia_activa.HPNDEFCAM:
            # FORMATO: "304 - GINECOBSTETRICIA"
            nombre = estancia_activa.HPNDEFCAM.HCANOMBRE
            habitacion = estancia_activa.HPNDEFCAM.HCANUMHABI
            if habitacion and habitacion.strip():
                cama_nombre = f"{habitacion} - {nombre}"
            else:
                cama_nombre = nombre

        # 4. Obtener Aseguradora (GENDETCON)
        aseguradora_nombre = None
        if ingreso_activo.GENDETCON_id: # Usar _id para evitar query si es nulo
            # Hacemos fetch si existe ID (Django lazy load lo haría, pero explícito es mejor para readonly)
            try:
                # Usamos getattr por si acaso el modelo no tiene la rel cargada por el ORM manager default
                det_con = ingreso_activo.GENDETCON 
                if det_con:
                    aseguradora_nombre = det_con.GDENOMBRE
            except Exception:
                pass

        # Construir nombre completo con todos los componentes
        nombres = f"{paciente_ext.PACPRINOM or ''} {paciente_ext.PACSEGNOM or ''}".strip()
        apellidos = f"{paciente_ext.PACPRIAPE or ''} {paciente_ext.PACSEGAPE or ''}".strip()
        nombre_completo = f"{nombres} {apellidos}".strip()
        
        # Obtener fecha de nacimiento
        fecha_nacimiento = None
        if paciente_ext.GPAFECNAC:
            fecha_nacimiento = paciente_ext.GPAFECNAC.date() if hasattr(paciente_ext.GPAFECNAC, 'date') else paciente_ext.GPAFECNAC
        
        return {
            'es_activo': True,
            'ingreso_id': ingreso_activo.AINCONSEC,
            'fecha_ingreso': ingreso_activo.AINFECING,
            'cama': cama_nombre,
            'aseguradora': aseguradora_nombre,
            'paciente_nombre': nombre_completo,
            'nombres': nombres,
            'apellidos': apellidos,
            'fecha_nacimiento': fecha_nacimiento,
            'edad': None # Se podría calcular si fuera necesario
        }

    except Exception as e:
        print(f"Error obteniendo info activa: {e}")
        return None

def buscar_pacientes_activos_filtro(query):
    """
    Busca pacientes que coincidan con el query (nombres o documento)
    Y que tengan un ingreso activo.
    """
    resultados = []
    
    try:
        if not query:
             # Traer ultimos 20 ingresos activos DE OBSTETRICIA
             # Primero buscamos las estancias activas de obstetricia y sus ingresos
            estancias_obs = Hpnestanc.objects.using('readonly').filter(
                HESFECSAL__isnull=True,
                HPNDEFCAM__HCANOMBRE__icontains='OBSTETRICIA'
            ).select_related('ADNINGRES', 'ADNINGRES__GENPACIEN', 'HPNDEFCAM').order_by('-OID')[:20]
            
            for est in estancias_obs:
                ing = est.ADNINGRES
                pac = ing.GENPACIEN
                resultados.append({
                    'documento': pac.PACNUMDOC,
                    'nombre_completo': f"{pac.PACPRINOM} {pac.PACSEGNOM or ''} {pac.PACPRIAPE} {pac.PACSEGAPE or ''}".strip(),
                    'ingreso': ing.AINCONSEC,
                    'fecha': ing.AINFECING,
                    'ingreso': ing.AINCONSEC,
                    'fecha': ing.AINFECING,
                    'cama': f"{est.HPNDEFCAM.HCANUMHABI} - {est.HPNDEFCAM.HCANOMBRE}" if est.HPNDEFCAM.HCANUMHABI else est.HPNDEFCAM.HCANOMBRE
                })
            return resultados

        else:
            # Buscar en Genpacien por documento o nombre
            q_filtro = Q(PACNUMDOC__icontains=query) | \
                       Q(PACPRINOM__icontains=query) | \
                       Q(PACPRIAPE__icontains=query) 

            # INTENTO DE BUSQUEDA POR CAMA (requiere join inverso complejo o busqueda separada)
            # Primero ver si el query parece numero de cama (digitos)
            ids_por_cama = []
            if query.replace('-', '').strip().isdigit() or len(query) < 5:
                 estancias_cama = Hpnestanc.objects.using('readonly').filter(
                    HESFECSAL__isnull=True,
                    HPNDEFCAM__HCANUMHABI__icontains=query,
                    HPNDEFCAM__HCANOMBRE__icontains='OBSTETRICIA' # Mantener filtro obstet? El usuario dijo "en esa area"
                 ).select_related('ADNINGRES')[:20]
                 ids_por_cama = [e.ADNINGRES.GENPACIEN_id for e in estancias_cama if e.ADNINGRES]

            pacientes = Genpacien.objects.using('readonly').filter(q_filtro)[:50]
            
            # Combinar IDs (los de nombre + los de cama)
            ids_pacientes = list(set([p.OID for p in pacientes] + ids_por_cama))
            ingresos = Adningreso.objects.using('readonly').filter(
                GENPACIEN__in=ids_pacientes,
                AINESTADO=0
            ).select_related('GENPACIEN').order_by('-AINFECING')
            
            for ing in ingresos:
                pac = ing.GENPACIEN
                # Verificar si tiene estancia activa? (Opcional, pero recomendado)
                # Y filtrar por OBSTETRICIA como solicitó el usuario
                estancia = Hpnestanc.objects.using('readonly').filter(
                    ADNINGRES=ing,
                    HESFECSAL__isnull=True,
                    HPNDEFCAM__HCANOMBRE__icontains='OBSTETRICIA' # FILTRO SOLICITADO
                ).select_related('HPNDEFCAM').first()
                
                # El usuario dijo "en Estancia hospitalaria, activos". Asumimos que requiere estancia abierta.
                if estancia:
                    nombre = estancia.HPNDEFCAM.HCANOMBRE
                    habitacion = estancia.HPNDEFCAM.HCANUMHABI
                    cama_str = f"{habitacion} - {nombre}" if (habitacion and habitacion.strip()) else nombre

                    resultados.append({
                        'documento': pac.PACNUMDOC,
                        'nombre_completo': f"{pac.PACPRINOM} {pac.PACSEGNOM or ''} {pac.PACPRIAPE} {pac.PACSEGAPE or ''}".strip(),
                        'ingreso': ing.AINCONSEC,
                        'fecha': ing.AINFECING,
                        'cama': cama_str
                    })
                
    except Exception as e:
        print(f"Error buscando activos: {e}")
        
    return resultados
