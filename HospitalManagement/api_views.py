from django.http import JsonResponse
from django.apps import apps
from django.db.models import Q
from datetime import datetime

# Use standard models
from consultas_externas.models import Genpacien, Adningreso, Hpnestanc, Hpndefcam, Hpnsubgru, Gendetcon
# New required models for diagnosis and vitals
from consultas_externas.models import Hcnfolio, Hcndiapac, Gendiagno, Hcnregenf

def calculate_age(born):
    if not born:
        return ""
    today = datetime.now()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def get_datos_antropometricos(paciente_oid):
    """
    Obtiene el peso y talla más recientes del paciente desde Hcnregenf
    """
    try:
        ultimo_reg = Hcnregenf.objects.using('readonly').filter(
            genpacien=paciente_oid
        ).exclude(hcrpeso=0, hcrtalla=0).order_by('-hcfecreg').first()
        
        if ultimo_reg:
            return {
                'peso': float(ultimo_reg.hcrpeso) if ultimo_reg.hcrpeso else None,
                'talla': float(ultimo_reg.hcrtalla) if ultimo_reg.hcrtalla else None
            }
    except Exception:
        pass
    return {'peso': None, 'talla': None}

def get_ultimo_diagnostico(paciente_oid):
    """
    Busca el último diagnóstico principal del paciente en Consultas Externas
    """
    try:
        # 1. Obtener el último folio
        ultimo_folio = Hcnfolio.objects.using('readonly').filter(
            genpacien=paciente_oid
        ).order_by('-hcfecfol').first()
        
        if not ultimo_folio:
            return ""
            
        # 2. Obtener el diagnóstico principal de ese folio
        diag_pac = Hcndiapac.objects.using('readonly').filter(
            hcnfolio=ultimo_folio.oid,
            hcpdiaprin=True
        ).first()
        
        if not diag_pac:
            # Si no hay principal, buscar el primero que aparezca
            diag_pac = Hcndiapac.objects.using('readonly').filter(
                hcnfolio=ultimo_folio.oid
            ).first()
            
        if not diag_pac:
            return ""
            
        # 3. Obtener el nombre desde Gendiagno
        diag_def = Gendiagno.objects.using('readonly').filter(oid=diag_pac.gendiagno).first()
        if diag_def:
            return f"{diag_def.diacodigo} - {diag_def.dianombre}"
            
        return ""
    except Exception:
        return ""

def query_paciente_enhanced(request):
    """
    API View for Enhanced Patient Search.
    Filters:
    - Active Patients (Adningreso open)
    - Returns: Doc, Name, Sala, Cama, BirthDate, Age, Insurer
    """
    try:
        term = request.GET.get('term', '')
        limit = int(request.GET.get('limit', 20))
        data = []
        
        if not term:
            # 1. Start with ALL Active Stays (Patients in a bed: ICU, Floors, etc.)
            active_stays = Hpnestanc.objects.using('readonly').filter(
                hesfecsal__isnull=True
            ).order_by('-hesfecing')[:500] # Usually < 400 total
            
            adm_oids = [s.adningres for s in active_stays if s.adningres]
            
            # 2. ALSO get very recent admissions (Transit/Arrivals) who might not have a bed yet
            recent_adms = Adningreso.objects.using('readonly').filter(
                ainfecegre__isnull=True
            ).order_by('-ainfecing')[:100]
            
            all_adm_oids = set(adm_oids)
            for a in recent_adms:
                all_adm_oids.add(a.oid)
            
            # Fetch all associated Admissions
            active_adms = Adningreso.objects.using('readonly').filter(oid__in=all_adm_oids)
            adm_map = {a.oid: a for a in active_adms}
            
            # Collect Patient IDs
            pac_ids = [a.genpacien_id for a in active_adms if a.genpacien_id]
            pacs = Genpacien.objects.using('readonly').filter(oid__in=pac_ids)
            pac_map = {p.oid: p for p in pacs}
            
            # Fetch Insurers
            detcon_ids = [a.gendetcon_id for a in active_adms if a.gendetcon_id]
            detcons = Gendetcon.objects.using('readonly').filter(oid__in=detcon_ids)
            detcon_map = {d.oid: d for d in detcons}

            # Map stays for fast access
            stay_map = {s.adningres: s for s in active_stays}

            # Prepare Helper Data for Beds/Rooms
            bed_ids = [s.hpndefcam for s in active_stays if s.hpndefcam]
            beds = Hpndefcam.objects.using('readonly').filter(oid__in=bed_ids)
            bed_map = {b.oid: b for b in beds}
            
            subgru_ids = [b.hpnsubgru for b in beds if b.hpnsubgru]
            subgrus = Hpnsubgru.objects.using('readonly').filter(oid__in=subgru_ids)
            subgru_map = {s.oid: s for s in subgrus}

            # Build Result List
            # We iterate over sorted admissions to keep newest first
            sorted_adms = sorted(active_adms, key=lambda x: x.ainfecing, reverse=True)
            
            for adm in sorted_adms:
                if not adm.genpacien_id: continue
                pac = pac_map.get(adm.genpacien_id)
                if not pac: continue
                detcon = detcon_map.get(adm.gendetcon_id)
                
                # Determine Location
                cama_nombre = "Sin Cama Asignada"
                sala_nombre = "En Admisión / Tránsito"
                
                stay = stay_map.get(adm.oid)
                if stay and stay.hpndefcam:
                    bed = bed_map.get(stay.hpndefcam)
                    if bed:
                        # Prioritizar códigos numéricos sobre nombres descriptivos de área
                        cama_nombre = bed.hcacodigo or bed.hcanumhabi or bed.hcanombre
                        # Si el nombre de la cama parece ser solo el nombre del área, intentar usar el código
                        if any(x in str(cama_nombre).upper() for x in ['URGENCIAS', 'OBSERVACION', 'PISO']):
                            if bed.hcacodigo and bed.hcacodigo.strip():
                                cama_nombre = bed.hcacodigo
                        if bed.hpnsubgru:
                            subgru = subgru_map.get(bed.hpnsubgru)
                            if subgru:
                                sala_nombre = subgru.hsunombre
                
                try:
                    edad = calculate_age(pac.gpafecnac)
                except:
                    edad = "N/A"
                
                full_name = f"{pac.pacprinom or ''} {pac.pacsegnom or ''} {pac.pacpriape or ''} {pac.pacsegape or ''}".strip()
                aseguradora = detcon.gdenombre if detcon else "Particular"
                
                item = {
                    'id': pac.oid, 
                    'text': full_name,
                    'paciente_id': pac.oid,
                    'documento': pac.pacnumdoc,
                    'nombre': full_name,
                    'sala': sala_nombre,
                    'cama': cama_nombre,
                    'fecha_nacimiento': pac.gpafecnac.strftime('%d/%m/%Y') if pac.gpafecnac else "",
                    'edad': str(edad),
                    'aseguradora': aseguradora,
                    'fecha_ingreso': adm.ainfecing.strftime('%d/%m/%Y') if adm.ainfecing else "",
                    'ingreso_id': adm.oid
                }
                data.append(item)

        else:
            # Search Active Admissions by Name/Doc
            # Cannot select_related genpacien! Must filter manually or use double query approach
            # Approach: Find Genpacien matching term -> Find Adningreso for those patients
            
            pacs = Genpacien.objects.using('readonly').filter(
                Q(pacnumdoc__icontains=term) | 
                Q(pacprinom__icontains=term) | 
                Q(pacpriape__icontains=term)
            )[:limit] # Find first N patients matching
            
            pac_map = {p.oid: p for p in pacs}
            pac_ids = list(pac_map.keys())
            
            if not pac_ids:
                return JsonResponse({'results': []})
            
            # Find Active Admissions for these patients
            qs = Adningreso.objects.using('readonly').filter(
                genpacien__in=pac_ids,
                ainfecegre__isnull=True
            ).order_by('-ainfecing')
            
            # Get Insurers
            detcon_ids = [a.gendetcon_id for a in qs if a.gendetcon_id]
            detcons = Gendetcon.objects.using('readonly').filter(oid__in=detcon_ids)
            detcon_map = {d.oid: d for d in detcons}

            for adm in qs:
                pac = pac_map.get(adm.genpacien_id)
                if not pac: continue
                detcon = detcon_map.get(adm.gendetcon_id)

                # Get latest active stay for this admission
                latest_estancia = Hpnestanc.objects.using('readonly').filter(
                    adningres=adm.oid, 
                    hesfecsal__isnull=True 
                ).order_by('-hesfecing').first()
                
                cama_nombre = ""
                sala_nombre = ""
                if latest_estancia:
                    if latest_estancia.hpndefcam:
                        cama_obj = Hpndefcam.objects.using('readonly').filter(oid=latest_estancia.hpndefcam).first()
                        if cama_obj:
                            cama_nombre = cama_obj.hcacodigo or cama_obj.hcanumhabi or cama_obj.hcanombre
                            if any(x in str(cama_nombre).upper() for x in ['URGENCIAS', 'OBSERVACION', 'PISO']):
                                if cama_obj.hcacodigo and cama_obj.hcacodigo.strip():
                                    cama_nombre = cama_obj.hcacodigo
                            if cama_obj.hpnsubgru:
                                 subgru_obj = Hpnsubgru.objects.using('readonly').filter(oid=cama_obj.hpnsubgru).first()
                                 if subgru_obj:
                                     sala_nombre = subgru_obj.hsunombre

                try:
                    edad = calculate_age(pac.gpafecnac)
                except:
                    edad = "N/A"
                
                full_name = f"{pac.pacprinom} {pac.pacsegnom or ''} {pac.pacpriape} {pac.pacsegape}".strip()
                aseguradora = detcon.gdenombre if detcon else "Particular"
                
                item = {
                    'id': pac.oid, 
                    'text': f"{pac.pacnumdoc} - {full_name}",
                    'paciente_id': pac.oid,
                    'documento': pac.pacnumdoc,
                    'nombre': full_name,
                    'sala': sala_nombre or "Sin Asignar",
                    'cama': cama_nombre or "Sin Asignar",
                    'fecha_nacimiento': pac.gpafecnac.strftime('%d/%m/%Y') if pac.gpafecnac else "",
                    'edad': str(edad),
                    'aseguradora': aseguradora,
                    'aseguradora': aseguradora,
                    'fecha_ingreso': adm.ainfecing.strftime('%d/%m/%Y') if adm.ainfecing else "",
                    'ingreso_id': adm.oid
                }
                data.append(item)
                
        return JsonResponse({'results': data})

    except Exception as e:
        return JsonResponse({'results': [], 'error': str(e)})

def query_tercero(request):
    term = request.GET.get('term', '')
    if not term: return JsonResponse({'results': []})
    try:
        Gentercer = apps.get_model('consultas_externas', 'Gentercer')
        results = Gentercer.objects.filter(
            Q(ternumdoc__icontains=term) | 
            Q(terprinom__icontains=term) | 
            Q(terpriape__icontains=term)
        ).values('oid', 'ternumdoc', 'terprinom', 'tersegnom', 'terpriape', 'tersegape')[:20]
        data = []
        for r in results:
            full_name = f"{r['terprinom'] or ''} {r['tersegnom'] or ''} {r['terpriape'] or ''} {r['tersegape'] or ''}".strip()
            data.append({'id': r['oid'], 'text': f"{r['ternumdoc']} - {full_name}"})
        return JsonResponse({'results': data})
    except Exception as e:
        return JsonResponse({'results': [], 'error': str(e)})

def get_tercero_details(request, oid):
    try:
        Gentercer = apps.get_model('consultas_externas', 'Gentercer')
        tercero = Gentercer.objects.get(pk=oid)
        full_name = f"{tercero.terprinom or ''} {tercero.tersegnom or ''} {tercero.terpriape or ''} {tercero.tersegape or ''}".strip()
        data = {
            'found': True, 'oid': tercero.pk, 'documento': tercero.ternumdoc,
            'nombre_completo': full_name, 'primerNombre': tercero.terprinom,
            'primerApellido': tercero.terpriape, 'fecha_nacimiento': ''
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'found': False, 'error': str(e)})

def get_diagnostico_paciente(request, oid):
    """
    Endpoint dedicado para obtener el último diagnóstico y datos antropométricos.
    Esto evita ralentizar las búsquedas masivas.
    """
    diag = get_ultimo_diagnostico(oid)
    antropometricos = get_datos_antropometricos(oid)
    return JsonResponse({
        'ultimo_diagnostico': diag,
        'peso': antropometricos['peso'],
        'talla': antropometricos['talla']
    })
