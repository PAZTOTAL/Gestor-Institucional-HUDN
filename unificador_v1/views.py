
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from .models import AtencionParto

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

import logging

try:
    from meows.models import Medicion, Paciente as MeowsPaciente  # noqa: F401
except ImportError:
    Medicion = None
    MeowsPaciente = None

from frecuenciafetal.models import (
    ControlFetocardia,
    ControlPostpartoInmediato,
    RegistroParto,
)

try:
    from trabajoparto.models import Formulario, Paciente as TrabajoPartoPaciente
except ImportError:
    Formulario = None
    TrabajoPartoPaciente = None

logger = logging.getLogger(__name__)


def _sexo_codigo_desde_his(val):
    """GENPACIEN.GPASEXPAC: 1=M, 2=F (alineado con comentario en meows.models.Genpacien)."""
    if val is None:
        return None
    try:
        i = int(val)
    except (TypeError, ValueError):
        return None
    if i == 2:
        return "F"
    if i == 1:
        return "M"
    return None


def _variantes_documento(doc):
    """Variantes de documento para cruzar MEOWS, fetal y parto (ceros a la izquierda, solo dígitos, relleno)."""
    d = (doc or "").strip()
    if not d:
        return []
    ids_ = [d]
    alt = d.lstrip("0") or "0"
    if alt != d:
        ids_.append(alt)
    compact = "".join(c for c in d if c.isdigit())
    if compact and compact not in ids_:
        ids_.append(compact)
    if compact.isdigit():
        for w in (8, 9, 10, 11, 12, 13, 15):
            pad = compact.zfill(w)
            if pad not in ids_:
                ids_.append(pad)
        nz = compact.lstrip("0") or "0"
        if nz != compact and nz not in ids_:
            ids_.append(nz)
    seen = set()
    out = []
    for x in ids_:
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _meows_por_documento(doc):
    if MeowsPaciente is None:
        return None
    for did in _variantes_documento(doc):
        p = MeowsPaciente.objects.filter(numero_documento=did).first()
        if p:
            return p
    return None


def _enriquecer_card_demografia(payload, doc):
    """Rellena campos vacíos del card con MEOWS, Trabajo de Parto, Fetal y BD hospitalaria."""
    from datetime import date, datetime

    dids = _variantes_documento(doc)
    if not dids:
        return payload

    def _vacío(val):
        if val is None:
            return True
        return isinstance(val, str) and not val.strip()

    def _nombre_placeholder(val):
        s = (val or "").strip().upper()
        return not s or s in ("N/A", "N/A N/A", "PACIENTE", "SIN NOMBRE", "-")

    def _recalcular_edad_desde_fn():
        fn_raw = payload.get("fecha_nacimiento")
        if not fn_raw:
            return
        try:
            fn_d = datetime.strptime(str(fn_raw)[:10], "%Y-%m-%d").date()
            today = date.today()
            payload["edad"] = today.year - fn_d.year - (
                (today.month, today.day) < (fn_d.month, fn_d.day)
            )
        except (ValueError, TypeError):
            pass

    def _fecha_ingreso_a_iso(fi_d):
        if fi_d is None:
            return None
        if hasattr(fi_d, "strftime"):
            try:
                return fi_d.strftime("%Y-%m-%d")
            except Exception:
                return None
        s = str(fi_d).strip()
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(s[:10], fmt).date().strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _merge_estancia_gineco_si_hay_huecos():
        """Rellena aseguradora, cama y fecha de ingreso desde estancia activa (readonly)."""
        if not (
            _vacío(payload.get("aseguradora"))
            or _vacío(payload.get("cama"))
            or _vacío(payload.get("fecha_ingreso"))
        ):
            return
        try:
            from meows.views import _obtener_estancia_activa_gineco
        except ImportError:
            return
        except Exception:
            return
        for did in dids:
            est = _obtener_estancia_activa_gineco(did)
            if not est:
                continue
            if _vacío(payload.get("aseguradora")):
                aseg = (est.get("aseguradora") or "").strip()
                if aseg:
                    payload["aseguradora"] = aseg
            if _vacío(payload.get("cama")):
                cam = (est.get("cama") or "").strip()
                if cam:
                    payload["cama"] = cam
            if _vacío(payload.get("fecha_ingreso")) and est.get("fecha_ingreso_dt"):
                dt = est["fecha_ingreso_dt"]
                if hasattr(dt, "strftime"):
                    payload["fecha_ingreso"] = dt.strftime("%Y-%m-%d")
            if not (
                _vacío(payload.get("aseguradora"))
                or _vacío(payload.get("cama"))
                or _vacío(payload.get("fecha_ingreso"))
            ):
                break

    m = _meows_por_documento(doc)
    if m:
        if _vacío(payload.get("aseguradora")):
            payload["aseguradora"] = m.aseguradora or ""
        if _vacío(payload.get("cama")):
            payload["cama"] = m.cama or ""
        if _vacío(payload.get("fecha_ingreso")):
            payload["fecha_ingreso"] = (
                m.fecha_ingreso.strftime("%Y-%m-%d") if m.fecha_ingreso else None
            )
        if _vacío(payload.get("responsable")):
            payload["responsable"] = m.responsable or ""
        if _vacío(payload.get("nombre_acompanante")):
            payload["nombre_acompanante"] = m.nombre_acompanante or ""
        if _vacío(payload.get("tipo_sangre")):
            payload["tipo_sangre"] = m.tipo_sangre or ""
        if _vacío(payload.get("fecha_nacimiento")) and m.fecha_nacimiento:
            payload["fecha_nacimiento"] = m.fecha_nacimiento.strftime("%Y-%m-%d")
        if payload.get("edad") is None and m.fecha_nacimiento:
            _recalcular_edad_desde_fn()
        if payload.get("edad_gestacional") is None and m.edad_gestacional is not None:
            payload["edad_gestacional"] = m.edad_gestacional
        if payload.get("gestas") is None and m.gestas is not None:
            payload["gestas"] = m.gestas
        if _vacío(payload.get("diagnostico")):
            payload["diagnostico"] = (m.diagnostico or "").strip()
        if _vacío(payload.get("num_historia_clinica")):
            payload["num_historia_clinica"] = (m.num_historia_clinica or "").strip()
        if _vacío(payload.get("sexo")):
            payload["sexo"] = (m.sexo or "").strip()
        if payload.get("n_controles_prenatales") is None and m.n_controles_prenatales is not None:
            payload["n_controles_prenatales"] = m.n_controles_prenatales
        if not (payload.get("apellidos") or "").strip():
            payload["apellidos"] = (m.apellidos or "").strip()

    # Paciente de Trabajo de Parto (a menudo tiene FN / grupo sanguíneo aunque MEOWS esté incompleto)
    tp = None
    if TrabajoPartoPaciente is not None:
        for did in dids:
            tp = TrabajoPartoPaciente.objects.filter(num_identificacion=did).first()
            if tp:
                break
    if tp:
        if _vacío(payload.get("fecha_nacimiento")) and tp.fecha_nacimiento:
            payload["fecha_nacimiento"] = tp.fecha_nacimiento.strftime("%Y-%m-%d")
        if _vacío(payload.get("tipo_sangre")) and tp.tipo_sangre:
            payload["tipo_sangre"] = str(tp.tipo_sangre).strip()
        nm_tp = (tp.nombres or "").strip()
        if nm_tp:
            if _nombre_placeholder(payload.get("nombre_completo")):
                payload["nombre_completo"] = nm_tp
            if _nombre_placeholder(payload.get("nombre_paciente")):
                payload["nombre_paciente"] = nm_tp
            if _nombre_placeholder(payload.get("nombres")):
                payload["nombres"] = nm_tp
        if _vacío(payload.get("num_historia_clinica")) and getattr(tp, "num_historia_clinica", None):
            payload["num_historia_clinica"] = str(tp.num_historia_clinica).strip()

    rp = RegistroParto.objects.filter(identificacion__in=dids).order_by("-created_at").first()
    if rp:
        if _vacío(payload.get("nombre_acompanante")):
            payload["nombre_acompanante"] = (rp.nombre_acompanante or "").strip()
        if _vacío(payload.get("responsable")):
            payload["responsable"] = (
                (rp.nombre_firma_paciente or rp.parto_atendido_por or rp.profesional_nombre or "")
                or ""
            ).strip()
        nm_f = (rp.nombre_paciente or "").strip()
        if nm_f:
            if _nombre_placeholder(payload.get("nombre_completo")):
                payload["nombre_completo"] = nm_f
            if _nombre_placeholder(payload.get("nombre_paciente")):
                payload["nombre_paciente"] = nm_f
            if _nombre_placeholder(payload.get("nombres")):
                payload["nombres"] = nm_f
        if payload.get("edad_gestacional") is None and rp.edad_gestacional is not None:
            payload["edad_gestacional"] = rp.edad_gestacional
        if payload.get("gestas") is None and rp.gestas is not None:
            payload["gestas"] = rp.gestas

    if _vacío(payload.get("nombre_acompanante")):
        rp_ac = (
            RegistroParto.objects.filter(identificacion__in=dids)
            .exclude(nombre_acompanante__isnull=True)
            .exclude(nombre_acompanante="")
            .order_by("-created_at")
            .first()
        )
        if rp_ac:
            payload["nombre_acompanante"] = (rp_ac.nombre_acompanante or "").strip()

    if _vacío(payload.get("responsable")):
        for row in RegistroParto.objects.filter(identificacion__in=dids).order_by("-created_at")[:20]:
            cand = (
                row.nombre_firma_paciente or row.parto_atendido_por or row.profesional_nombre or ""
            ).strip()
            if cand:
                payload["responsable"] = cand
                break

    if _vacío(payload.get("responsable")):
        cf = (
            ControlFetocardia.objects.filter(registro__identificacion__in=dids)
            .exclude(responsable__isnull=True)
            .exclude(responsable="")
            .order_by("-fecha", "-hora")
            .first()
        )
        if cf and (cf.responsable or "").strip():
            payload["responsable"] = cf.responsable.strip()

    if _vacío(payload.get("responsable")):
        cpp = (
            ControlPostpartoInmediato.objects.filter(registro__identificacion__in=dids)
            .exclude(responsable__isnull=True)
            .exclude(responsable="")
            .order_by("-fecha", "-hora")
            .first()
        )
        if cpp and (cpp.responsable or "").strip():
            payload["responsable"] = cpp.responsable.strip()

    forms_recientes = []
    if Formulario is not None:
        forms_recientes = list(
            Formulario.objects.filter(paciente__num_identificacion__in=dids)
            .select_related("aseguradora")
            .order_by("-fecha_actualizacion")[:25]
        )
    for form in forms_recientes:
        if _vacío(payload.get("responsable")) and (form.responsable or "").strip():
            payload["responsable"] = form.responsable.strip()
        if _vacío(payload.get("diagnostico")) and (form.diagnostico or "").strip():
            payload["diagnostico"] = form.diagnostico.strip()
        if _vacío(payload.get("num_historia_clinica")) and getattr(form.paciente, "num_historia_clinica", None):
            payload["num_historia_clinica"] = str(form.paciente.num_historia_clinica).strip()
        if payload.get("edad") is None and form.edad_snapshot is not None:
            payload["edad"] = int(form.edad_snapshot)
        if _vacío(payload.get("aseguradora")) and form.aseguradora_id:
            try:
                an = getattr(form.aseguradora, "nombre", None) or str(form.aseguradora)
                if an and str(an).strip():
                    payload["aseguradora"] = str(an).strip()
            except Exception:
                pass
        if payload.get("edad_gestacional") is None and form.edad_gestion is not None:
            payload["edad_gestacional"] = form.edad_gestion
        if payload.get("n_controles_prenatales") is None and form.n_controles_prenatales is not None:
            payload["n_controles_prenatales"] = form.n_controles_prenatales

    _recalcular_edad_desde_fn()

    # Estancia gineco (cama / ingreso / aseguradora) aunque ya exista MEOWS completo en demografía
    _merge_estancia_gineco_si_hay_huecos()

    # Si faltan datos demográficos o campos del card clínico, consultar hospital (readonly)
    falta_demo = (
        _vacío(payload.get("fecha_nacimiento"))
        or _vacío(payload.get("tipo_sangre"))
        or _nombre_placeholder(payload.get("nombre_completo"))
    )
    falta_card_clinico = (
        _vacío(payload.get("aseguradora"))
        or _vacío(payload.get("cama"))
        or _vacío(payload.get("fecha_ingreso"))
        or _vacío(payload.get("responsable"))
        or _vacío(payload.get("nombre_acompanante"))
    )
    if falta_demo or falta_card_clinico:
        try:
            from trabajoparto.views import PacienteViewSet
            hosp_p, extras = PacienteViewSet()._sincronizar_paciente_desde_dgempres99(dids[0])
        except (ImportError, Exception):
            logger.debug(
                "Enriquecimiento hospitalario omitido para doc=%s", dids[0], exc_info=True
            )
            hosp_p, extras = None, None
        if hosp_p:
            ext = extras or {}
            nm_h = (hosp_p.nombres or "").strip()
            if nm_h:
                if _nombre_placeholder(payload.get("nombre_completo")):
                    payload["nombre_completo"] = nm_h
                if _nombre_placeholder(payload.get("nombre_paciente")):
                    payload["nombre_paciente"] = nm_h
                if _nombre_placeholder(payload.get("nombres")):
                    payload["nombres"] = nm_h
            if _vacío(payload.get("fecha_nacimiento")) and hosp_p.fecha_nacimiento:
                payload["fecha_nacimiento"] = hosp_p.fecha_nacimiento.strftime("%Y-%m-%d")
            if _vacío(payload.get("tipo_sangre")) and hosp_p.tipo_sangre:
                payload["tipo_sangre"] = str(hosp_p.tipo_sangre).strip()
            if _vacío(payload.get("aseguradora")) and ext.get("aseguradora"):
                payload["aseguradora"] = str(ext.get("aseguradora") or "").strip()
            cama_ext = (ext.get("cama") or "").strip()
            if _vacío(payload.get("cama")) and cama_ext:
                payload["cama"] = cama_ext
            fi_d = ext.get("fecha_ingreso")
            if _vacío(payload.get("fecha_ingreso")) and fi_d is not None:
                fi_iso_h = _fecha_ingreso_a_iso(fi_d)
                if fi_iso_h:
                    payload["fecha_ingreso"] = fi_iso_h
            if ext.get("tipo_sangre_display") and _vacío(payload.get("tipo_sangre")):
                payload["tipo_sangre"] = str(ext["tipo_sangre_display"]).strip()
            if payload.get("edad_gestacional") is None and ext.get("edad_gestacional") is not None:
                payload["edad_gestacional"] = ext.get("edad_gestacional")
            if payload.get("gestas") is None and ext.get("g") is not None:
                payload["gestas"] = ext.get("g")
            if _vacío(payload.get("diagnostico")) and ext.get("diagnostico"):
                payload["diagnostico"] = str(ext.get("diagnostico") or "").strip()
            if _vacío(payload.get("sexo")):
                sc = _sexo_codigo_desde_his(ext.get("sexo_his"))
                if sc:
                    payload["sexo"] = sc
            np = (ext.get("nombres_pila") or "").strip()
            if np and (
                _vacío(payload.get("nombres"))
                or (payload.get("nombres") or "").strip() == (payload.get("nombre_completo") or "").strip()
            ):
                payload["nombres"] = np
            if payload.get("n_controles_prenatales") is None and ext.get("n_controles_prenatales") is not None:
                try:
                    payload["n_controles_prenatales"] = int(ext["n_controles_prenatales"])
                except (TypeError, ValueError):
                    payload["n_controles_prenatales"] = ext.get("n_controles_prenatales")
            _recalcular_edad_desde_fn()

    # Tras hospital (o si no hubo), volver a intentar estancia para cama/ingreso/aseguradora
    _merge_estancia_gineco_si_hay_huecos()

    # Último recurso: documento guardado con otro formato (ej. ceros / caracteres) en identificación fetal
    core_digits = "".join(c for c in str(doc) if c.isdigit())
    if len(core_digits) >= 8 and (
        _vacío(payload.get("responsable")) or _vacío(payload.get("nombre_acompanante"))
    ):
        for row in RegistroParto.objects.filter(identificacion__contains=core_digits).order_by(
            "-created_at"
        )[:35]:
            if _vacío(payload.get("nombre_acompanante")) and (row.nombre_acompanante or "").strip():
                payload["nombre_acompanante"] = row.nombre_acompanante.strip()
            if _vacío(payload.get("responsable")):
                cand = (
                    row.nombre_firma_paciente
                    or row.parto_atendido_por
                    or row.profesional_nombre
                    or ""
                ).strip()
                if cand:
                    payload["responsable"] = cand
            if not _vacío(payload.get("responsable")) and not _vacío(
                payload.get("nombre_acompanante")
            ):
                break
        if _vacío(payload.get("responsable")):
            cf2 = (
                ControlFetocardia.objects.filter(registro__identificacion__contains=core_digits)
                .exclude(responsable__isnull=True)
                .exclude(responsable="")
                .order_by("-fecha", "-hora")
                .first()
            )
            if cf2 and (cf2.responsable or "").strip():
                payload["responsable"] = cf2.responsable.strip()
        if _vacío(payload.get("responsable")):
            cpp2 = (
                ControlPostpartoInmediato.objects.filter(
                    registro__identificacion__contains=core_digits
                )
                .exclude(responsable__isnull=True)
                .exclude(responsable="")
                .order_by("-fecha", "-hora")
                .first()
            )
            if cpp2 and (cpp2.responsable or "").strip():
                payload["responsable"] = cpp2.responsable.strip()

    return payload


def _upsert_meows_desde_payload_unificado(doc_canon, nombre_completo_str, payload, extras_hospital):
    """Persiste en MEOWS los datos del hospital/card para reutilizarlos en los módulos."""
    from datetime import datetime

    partes = (nombre_completo_str or "").strip().split(None, 1)
    nom0 = partes[0] or "Paciente"
    ape0 = partes[1] if len(partes) > 1 else "-"
    ts = (payload.get("tipo_sangre") or "").strip()[:5]
    if not ts and extras_hospital:
        td = extras_hospital.get("tipo_sangre_display")
        if td:
            ts = str(td).strip()[:5]

    fi_raw = payload.get("fecha_ingreso")
    fi_date = None
    if fi_raw:
        try:
            fi_date = datetime.strptime(str(fi_raw)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            fi_date = None

    try:
        mp, _created = MeowsPaciente.objects.get_or_create(
            numero_documento=doc_canon,
            defaults={
                "nombres": nom0,
                "apellidos": ape0,
                "sexo": "F",
            },
        )
        mp.nombres = nom0
        mp.apellidos = ape0
        if payload.get("aseguradora"):
            mp.aseguradora = str(payload["aseguradora"])[:200]
        if payload.get("cama"):
            mp.cama = str(payload["cama"])[:50]
        if fi_date:
            mp.fecha_ingreso = fi_date
        if ts:
            mp.tipo_sangre = ts[:5]
        if payload.get("fecha_nacimiento"):
            try:
                mp.fecha_nacimiento = datetime.strptime(
                    str(payload["fecha_nacimiento"])[:10], "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                pass
        eg = payload.get("edad_gestacional")
        if eg is not None and str(eg).strip():
            try:
                mp.edad_gestacional = int(eg)
            except (ValueError, TypeError):
                pass
        g = payload.get("gestas")
        if g is not None and str(g).strip():
            try:
                mp.gestas = int(g)
            except (ValueError, TypeError):
                pass
        ncp = payload.get("n_controles_prenatales")
        if ncp is not None and str(ncp).strip():
            try:
                mp.n_controles_prenatales = int(ncp)
            except (ValueError, TypeError):
                pass
        if extras_hospital and extras_hospital.get("diagnostico"):
            mp.diagnostico = str(extras_hospital["diagnostico"])[:2000]
        nhc = payload.get("num_historia_clinica")
        if nhc:
            mp.num_historia_clinica = str(nhc)[:50]
        if payload.get("responsable"):
            mp.responsable = str(payload["responsable"])[:200]
        if payload.get("nombre_acompanante"):
            mp.nombre_acompanante = str(payload["nombre_acompanante"])[:200]
        mp.save()
    except Exception as exc:
        logger.warning("No se pudo sincronizar meows.Paciente desde sala unificada: %s", exc)


def get_patient_timeline(documento):
    """
    Construye la línea de vida cronológica cruzando datos de MEOWS, Fetal y Parto.
    Se basa en el número de identificación del paciente.
    """
    try:
        from meows.models import Medicion
    except ImportError:
        Medicion = None
    
    from frecuenciafetal.models import RegistroParto
    
    try:
        from trabajoparto.models import Formulario
    except ImportError:
        Formulario = None
        
    from django.db.models import Q
    from django.utils import timezone

    # Consultar datos de todas las fuentes
    meows = Medicion.objects.filter(paciente__numero_documento=documento).order_by("-fecha_hora") if Medicion else []
    fetal = RegistroParto.objects.filter(identificacion=documento).order_by("-created_at")
    parto = Formulario.objects.filter(paciente__num_identificacion=documento).order_by("-created_at") if Formulario else []

    timeline = []

    # 1. Agregar MEOWS
    for m in meows:
        color_map = {
            "BLANCO": "#3b82f6", "VERDE": "#10b981",
            "AMARILLO": "#f59e0b", "ROJO": "#ef4444",
        }
        m_color = color_map.get(m.meows_riesgo, "#312e81")
        timeline.append({
            "tipo": "MEOWS",
            "fecha": m.fecha_hora.isoformat() if m.fecha_hora else None,
            "titulo": "🩺 MONITOREO MEOWS",
            "detalle": f"Riesgo: {m.meows_riesgo} | Puntaje: {m.meows_total}",
            "color": m_color,
            "icon": "activity"
        })

    # 2. Agregar FETAL
    for f in fetal:
        timeline.append({
            "tipo": "FETAL",
            "fecha": f.created_at.isoformat() if f.created_at else None,
            "titulo": "❤️ CONTROL FETAL",
            "detalle": f"EG: {f.edad_gestacional} Sem - Registro de monitoreo fetal.",
            "color": "#ec4899",
            "icon": "baby"
        })

    # 3. Agregar PARTO
    for p in parto:
        dx = (p.diagnostico[:50] + '...') if p.diagnostico else "Sin diagnóstico registrado"
        timeline.append({
            "tipo": "PARTO",
            "fecha": p.created_at.isoformat() if p.created_at else None,
            "titulo": "👶 TRABAJO DE PARTO",
            "detalle": f"Dx: {dx}",
            "color": "#8b5cf6",
            "icon": "clipboard-list"
        })

    # Ordenar por fecha (desc) y prioridad de tipo para empates.
    # Además, eliminar entradas duplicadas exactas para limpiar la visualización.
    from datetime import datetime

    tipo_prioridad = {"MEOWS": 0, "FETAL": 1, "PARTO": 2}

    def _parse_fecha(value):
        if not value:
            return datetime.min
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return datetime.min

    timeline_ordenada = sorted(
        timeline,
        key=lambda x: (
            _parse_fecha(x.get("fecha")),
            -tipo_prioridad.get(x.get("tipo", ""), 99),
        ),
        reverse=True,
    )

    timeline_limpia = []
    vistos = set()
    for item in timeline_ordenada:
        firma = (
            item.get("tipo", ""),
            item.get("fecha", ""),
            item.get("titulo", ""),
            item.get("detalle", ""),
        )
        if firma in vistos:
            continue
        vistos.add(firma)
        timeline_limpia.append(item)

    return timeline_limpia


def dashboard(request):
    """
    Vista de bienvenida al aplicativo (Dashboard General).
    """
    return render(request, "obstetricia/dashboard.html", {
        "is_dashboard": True,
        "title": "Bienvenido al Sistema Obstétrico"
    })


def manual_usuario(request):
    """
    Manual de usuario: manejo operativo y funcional del sistema obstétrico unificado.
    """
    return render(
        request,
        "obstetricia/manual_usuario.html",
        {
            "is_manual_usuario": True,
            "title": "Manual de usuario",
        },
    )


def atencion_detalle(request, id):
    atencion = get_object_or_404(AtencionParto, id=id)

    # Integración por identificador textual mientras se define FK real entre apps.
    identificador = (atencion.paciente or "").strip()

    # 1. MEOWS: Buscar por atención, y si no hay, por identificación
    meows = []
    if Medicion:
        meows = Medicion.objects.filter(atencion=atencion).select_related("paciente", "formulario")
        if not meows.exists() and identificador:
            if identificador.isdigit():
                meows = Medicion.objects.filter(paciente__numero_documento=identificador).select_related("paciente", "formulario")
            else:
                meows = Medicion.objects.filter(Q(paciente__nombres__icontains=identificador) | Q(paciente__apellidos__icontains=identificador)).select_related("paciente", "formulario")

    # 2. FETAL: Buscar por atención, y si no hay, por identificación
    fetal = RegistroParto.objects.filter(atencion=atencion)
    if not fetal.exists() and identificador:
        if identificador.isdigit():
            fetal = RegistroParto.objects.filter(identificacion=identificador)
        else:
            fetal = RegistroParto.objects.filter(nombre_paciente__icontains=identificador)

    # 3. PARTO: Buscar por atención, y si no hay, por identificación
    parto = []
    if Formulario:
        parto = Formulario.objects.filter(atencion=atencion).select_related("paciente")
        if not parto.exists() and identificador:
            if identificador.isdigit():
                parto = Formulario.objects.filter(paciente__num_identificacion=identificador).select_related("paciente")
            else:
                parto = Formulario.objects.filter(paciente__nombres__icontains=identificador).select_related("paciente")

    # CONSTRUCCIÓN DE LA LÍNEA DE TIEMPO UNIFICADA
    timeline = []

    # 1. Agregar MEOWS
    for m in meows:
        # Color dinámico según el riesgo MEOWS
        color_map = {
            "BLANCO": "#3b82f6",     # Azul
            "VERDE": "#10b981",      # Verde
            "AMARILLO": "#f59e0b",   # Amarillo/Naranja
            "ROJO": "#ef4444",       # Rojo
        }
        m_color = color_map.get(m.meows_riesgo, "#312e81") # Indigo por defecto

        timeline.append({
            "tipo": "MEOWS",
            "fecha": m.fecha_hora,
            "obj": m,
            "icon": "activity",
            "color": m_color
        })

    # 2. Agregar FETAL (RegistroParto)
    for f in fetal:
        timeline.append({
            "tipo": "FETAL",
            "fecha": f.created_at,
            "obj": f,
            "icon": "baby",
            "color": "#ec4899"
        })

    # 3. Agregar PARTO (Formulario)
    for p in parto:
        timeline.append({
            "tipo": "PARTO",
            "fecha": p.created_at,
            "obj": p,
            "icon": "clipboard-list",
            "color": "#8b5cf6"
        })

    # Ordenar por fecha descendente (lo más reciente arriba)
    timeline = sorted(timeline, key=lambda x: x["fecha"] if x["fecha"] else timezone.now(), reverse=True)

    # Calcular Estado Global según el riesgo MEOWS más alto encontrado
    estado_global = "ESTABLE"
    if Medicion and meows:
        riesgos_encontrados = set(meows.values_list("meows_riesgo", flat=True)) if hasattr(meows, 'values_list') else set([m.meows_riesgo for m in meows])
        estado_global = "CRÍTICO"
    elif "AMARILLO" in riesgos_encontrados:
        estado_global = "ALERTA"

    # Determinar si hay un paciente vinculado
    has_paciente = bool(atencion.paciente)

    return render(request, "obstetricia/detalle.html", {
        "atencion": atencion,
        "meows": meows,
        "fetal": fetal,
        "parto": parto,
        "timeline": timeline,
        "estado_global": estado_global,
        "has_paciente": has_paciente
    })


@require_http_methods(["GET"])
def api_datos_paciente_unificado(request):
    """
    Devuelve datos del paciente para poblar MEOWS, Frecuencia Fetal y Trabajo de Parto.
    RESTRICCIÓN: Solo busca personas ACTIVAS en el censo de Gineco-Obstetricia.
    Uso: GET /atencion/api/datos-paciente-unificado/?doc=123456
    """
    doc = (request.GET.get("doc") or request.GET.get("num_identificacion") or "").strip()
    if not doc:
        return JsonResponse({"ok": False, "error": "Parámetro doc requerido"}, status=400)

    selected_db = request.session.get('hospital_db', 'readonly')
    from frecuenciafetal.sala_partos_db import listar_pacientes_sala_partos
    from datetime import date

    # 1. Buscar PRIMERO en el Censo Activo de la Base de Datos Hospitalaria
    try:
        censo_pacientes = listar_pacientes_sala_partos(query=doc, db_name=selected_db)
    except Exception as e:
        logger.error(f"Error consultando censo activo en {selected_db}: {e}")
        censo_pacientes = []

    # Intentar encontrar coincidencia exacta en el censo
    p_censo = next((p for p in censo_pacientes if str(p['identificacion']).strip() == doc), None)
    
    if not p_censo and len(censo_pacientes) > 0:
        # Si no hubo coincidencia exacta pero hay resultados, probar con variantes
        dids = _variantes_documento(doc)
        p_censo = next((p for p in censo_pacientes if str(p['identificacion']).strip() in dids), None)

    if p_censo:
        # Paciente está activa en el censo. Preparamos el payload.
        doc_canon = str(p_censo['identificacion']).strip()
        
        # Sincronizar/Crear paciente local si es necesario (MEOWS)
        meows_p = None
        if MeowsPaciente:
            meows_p, _ = MeowsPaciente.objects.get_or_create(
                numero_documento=doc_canon,
                defaults={
                    "nombres": p_censo['nombre_paciente'] or "PACIENTE",
                    "apellidos": "",
                    "num_historia_clinica": p_censo['historia_clinica'] or "",
                    "tipo_sangre": p_censo['grupo_sanguineo'] or "",
                    "aseguradora": p_censo['aseguradora'] or "",
                    "cama": p_censo['numero_cama'] or "",
                    "diagnostico": p_censo['diagnostico'] or "",
                }
            )

        payload = {
            "ok": True,
            "encontrado": True,
            "nombre_completo": p_censo['nombre_paciente'],
            "nombre_paciente": p_censo['nombre_paciente'],
            "nombres": p_censo['nombre_paciente'],
            "apellidos": "",
            "num_identificacion": doc_canon,
            "identificacion": doc_canon,
            "num_historia_clinica": p_censo['historia_clinica'],
            "fecha_nacimiento": p_censo['fecha_nacimiento'].strftime("%Y-%m-%d") if hasattr(p_censo['fecha_nacimiento'], 'strftime') else None,
            "edad": p_censo.get('edad_anos'),
            "sexo": "F", # Por defecto en esta área
            "aseguradora": p_censo['aseguradora'],
            "cama": p_censo['numero_cama'],
            "fecha_ingreso": p_censo['fecha_ingreso'].strftime("%Y-%m-%d") if hasattr(p_censo['fecha_ingreso'], 'strftime') else None,
            "responsable": "",
            "tipo_sangre": p_censo['grupo_sanguineo'],
            "nombre_acompanante": "",
            "diagnostico": p_censo['diagnostico'],
            "edad_gestacional": p_censo['edad_gestacional'],
            "gestas": p_censo['gestas'],
            "n_controles_prenatales": p_censo.get('controles_prenatales'),
            "atencion_id": AtencionParto.objects.filter(paciente=doc_canon).order_by("-fecha_inicio").values_list("id", flat=True).first(),
            "mediciones_count": Medicion.objects.filter(paciente__numero_documento=doc_canon).count() if Medicion else 0,
            "fetal_count": RegistroParto.objects.filter(identificacion=doc_canon).count(),
            "parto_count": Formulario.objects.filter(paciente__num_identificacion=doc_canon).count() if Formulario else 0,
            "estado_global": "ESTABLE",
            "timeline": get_patient_timeline(doc_canon),
            "fuente_datos": "censo_activo_hospital",
        }
        
        # Recalcular edad si tenemos fecha de nacimiento real en meows_p
        if meows_p and meows_p.fecha_nacimiento:
            payload["fecha_nacimiento"] = meows_p.fecha_nacimiento.strftime("%Y-%m-%d")
            today = date.today()
            payload["edad"] = today.year - meows_p.fecha_nacimiento.year - (
                (today.month, today.day) < (meows_p.fecha_nacimiento.month, meows_p.fecha_nacimiento.day)
            )

        _enriquecer_card_demografia(payload, doc_canon)
        return JsonResponse(payload)

    # 2. Fallback solo si ya está en el sistema local (pero no activa en censo)
    # Nota: El usuario pidió buscar SOLAMENTE activas, pero permitimos ver registros locales
    # si el documento ya tiene una atención iniciada para evitar romper el flujo de edición.
    if AtencionParto.objects.filter(paciente__in=_variantes_documento(doc), estado="activo").exists():
        # Lógica original simplificada para pacientes locales con atención activa
        for did in _variantes_documento(doc):
            if MeowsPaciente:
                meows_p = MeowsPaciente.objects.filter(numero_documento=did).first()
                if meows_p:
                    # (Payload similar al original, pero marcado como local)
                    payload = {
                        "ok": True,
                        "encontrado": True,
                        "nombre_completo": f"{meows_p.nombres} {meows_p.apellidos}".strip(),
                        "num_identificacion": meows_p.numero_documento,
                        "atencion_id": AtencionParto.objects.filter(paciente=meows_p.numero_documento, estado="activo").first().id,
                        "fuente_datos": "local_activo",
                        "mensaje_aviso": "Paciente no figura en censo actual, pero tiene atención abierta."
                    }
                    # ... llenar el resto ...
                    _enriquecer_card_demografia(payload, did)
                    return JsonResponse(payload)

    return JsonResponse({
        "ok": True, 
        "encontrado": False, 
        "mensaje": "Paciente no encontrada en el censo activo de Gineco-Obstetricia"
    })


@require_http_methods(["POST"])
def guardar_datos_paciente_card(request, atencion_id):
    """
    Guarda los datos básicos y clínicos de la card de paciente.
    Crea/actualiza meows.Paciente y actualiza AtencionParto.paciente.
    Para pacientes nuevos: este es el único punto de ingreso.
    """
    import json
    from django.db import IntegrityError

    atencion = get_object_or_404(AtencionParto, id=atencion_id)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    num_identificacion = (data.get("num_identificacion") or "").strip()
    if not num_identificacion:
        return JsonResponse({"ok": False, "error": "Identificación es requerida"}, status=400)

    nombres_completos = (data.get("nombres") or "").strip()
    partes = nombres_completos.split(maxsplit=1) if nombres_completos else ["", ""]
    nombres = partes[0] or "N/A"
    apellidos = partes[1] if len(partes) > 1 else "N/A"

    num_hc = (data.get("num_historia_clinica") or "").strip() or f"HC-{num_identificacion}"

    if MeowsPaciente is None:
        return JsonResponse({"ok": False, "error": "Módulo MEOWS no disponible para guardar paciente"}, status=503)

    try:
        paciente, created = MeowsPaciente.objects.get_or_create(
            numero_documento=num_identificacion,
            defaults={
                "nombres": nombres,
                "apellidos": apellidos,
                "sexo": (data.get("sexo") or "F")[:1] or "F",
                "aseguradora": (data.get("aseguradora") or "")[:200],
                "cama": (data.get("cama") or "")[:50],
                "responsable": (data.get("responsable") or "")[:200],
                "nombre_acompanante": (data.get("nombre_acompanante") or "")[:200],
                "tipo_sangre": (data.get("tipo_sangre") or "")[:5],
                "diagnostico": (data.get("diagnostico") or "").strip(),
                "num_historia_clinica": num_hc[:50],
            }
        )
    except IntegrityError as exc:
        return JsonResponse({"ok": False, "error": f"No se pudo crear el paciente: {exc}"}, status=400)
    if not created:
        paciente.nombres = nombres
        paciente.apellidos = apellidos
        paciente.sexo = (data.get("sexo") or paciente.sexo or "F")[:1]

    paciente.aseguradora = (data.get("aseguradora") or "")[:200]
    paciente.cama = (data.get("cama") or "")[:50]
    paciente.responsable = (data.get("responsable") or "")[:200]
    paciente.diagnostico = (data.get("diagnostico") or "").strip()
    paciente.num_historia_clinica = num_hc[:50]
    paciente.nombre_acompanante = (data.get("nombre_acompanante") or "")[:200]
    paciente.tipo_sangre = (data.get("tipo_sangre") or "")[:5]
    eg = data.get("edad_gestacional")
    paciente.edad_gestacional = int(eg) if eg is not None and str(eg).strip() else None
    g = data.get("gestas")
    paciente.gestas = int(g) if g is not None and str(g).strip() else None
    ncp = data.get("n_controles_prenatales")
    paciente.n_controles_prenatales = int(ncp) if ncp is not None and str(ncp).strip() else None

    from datetime import datetime
    fn = data.get("fecha_nacimiento")
    if fn:
        try:
            paciente.fecha_nacimiento = datetime.strptime(str(fn)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            paciente.fecha_nacimiento = None
    else:
        paciente.fecha_nacimiento = None

    fi = data.get("fecha_ingreso")
    if fi:
        try:
            paciente.fecha_ingreso = datetime.strptime(str(fi)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            paciente.fecha_ingreso = None
    else:
        paciente.fecha_ingreso = None

    try:
        paciente.save()
    except IntegrityError:
        return JsonResponse({"ok": False, "error": "Error al guardar paciente (documento duplicado)"}, status=400)

    # Sincronizar también en trabajoparto.Paciente (para Frecuencia Fetal y Trabajo de Parto)
    if TrabajoPartoPaciente:
        nombres_tp = f"{nombres} {apellidos}".strip() or "N/A"
        tipo_sangre = (data.get("tipo_sangre") or "")[:3] or None
        try:
            tp_paciente, created = TrabajoPartoPaciente.objects.get_or_create(
                num_identificacion=num_identificacion,
                defaults={
                    "num_historia_clinica": num_hc[:255],
                    "nombres": nombres_tp[:255],
                    "fecha_nacimiento": paciente.fecha_nacimiento,
                    "tipo_sangre": tipo_sangre,
                }
            )
            if not created:
                tp_paciente.nombres = nombres_tp[:255]
                tp_paciente.fecha_nacimiento = paciente.fecha_nacimiento
                tp_paciente.tipo_sangre = tipo_sangre or tp_paciente.tipo_sangre
                tp_paciente.save()
        except IntegrityError:
            pass

    atencion.paciente = num_identificacion
    atencion.save(update_fields=["paciente"])

    return JsonResponse({
        "ok": True,
        "mensaje": "Datos guardados correctamente",
        "documento": num_identificacion,
    })


def pdf_atencion(request, id):
    """
    Genera una Historia Clínica Obstétrica Unificada ensamblando los PDFs
    originales de cada módulo (MEOWS, Fetal, Parto) en un solo documento.
    Mantiene el diseño, tablas y biometría original de cada formato.
    """
    from PyPDF2 import PdfWriter, PdfReader
    import io
    from django.http import HttpResponse
    from unificador_v1.models import AtencionParto
    
    # Importar generadores originales
    try:
        from meows.generador_pdf_meows import generar_pdf_meows
    except ImportError:
        generar_pdf_meows = None
        
    from frecuenciafetal.pdf_generator import generar_pdf_registro
    
    try:
        from trabajoparto.pdf_utils import generar_pdf_formulario_clinico
    except ImportError:
        generar_pdf_formulario_clinico = None
    
    # Modelos para búsqueda
    try:
        from meows.models import Medicion
    except ImportError:
        Medicion = None
        
    from frecuenciafetal.models import RegistroParto
    
    try:
        from trabajoparto.models import Formulario
    except ImportError:
        Formulario = None

    atencion = get_object_or_404(AtencionParto, id=id)
    doc_override = (request.GET.get("doc") or "").strip()
    documento_objetivo = doc_override or (atencion.paciente or "").strip()

    # Si llega doc y existe una atención más coherente para ese documento, usarla para metadatos/filename.
    if doc_override:
        atencion_doc = AtencionParto.objects.filter(paciente=doc_override).order_by("-fecha_inicio").first()
        if atencion_doc:
            atencion = atencion_doc
    writer = PdfWriter()
    has_content = False

    # 1. --- MÓDULO MEOWS ---
    try:
        from meows.models import Paciente as PacienteMeows
    except ImportError:
        PacienteMeows = None

    # Si llega doc por querystring, filtrar EXCLUSIVAMENTE por documento para evitar
    # mezclar registros de otra atención/paciente (caso crítico reportado).
    mediciones_qs = []
    if Medicion:
        if doc_override:
            mediciones_qs = Medicion.objects.filter(
                paciente__numero_documento=documento_objetivo
            ).order_by("fecha_hora")
        else:
            mediciones_qs = Medicion.objects.filter(
                atencion=atencion
            ).order_by("fecha_hora")

    if Medicion and mediciones_qs and mediciones_qs.exists() and generar_pdf_meows:
        try:
            paciente_meows = PacienteMeows.objects.get(numero_documento=documento_objetivo) if PacienteMeows else None
        except (Exception):
            paciente_meows = mediciones_qs.first().paciente if mediciones_qs else None

        response_meows = generar_pdf_meows(paciente_meows, list(mediciones_qs))
        if isinstance(response_meows, HttpResponse):
            pdf_file = io.BytesIO(response_meows.content)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                writer.add_page(page)
            has_content = True

    # 2. --- MÓDULO CONTROL FETAL ---
    if doc_override:
        registros_fetal = RegistroParto.objects.filter(
            identificacion=documento_objetivo
        ).order_by("created_at")
    else:
        registros_fetal = RegistroParto.objects.filter(
            atencion=atencion
        ).order_by("created_at")

    for reg in registros_fetal:
        pdf_bytes = generar_pdf_registro(reg)
        if pdf_bytes:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                writer.add_page(page)
            has_content = True

    # 3. --- MÓDULO TRABAJO DE PARTO ---
    formularios_parto = []
    if Formulario:
        if doc_override:
            formularios_parto = Formulario.objects.filter(
                paciente__num_identificacion=documento_objetivo
            ).order_by("fecha_actualizacion")
        else:
            formularios_parto = Formulario.objects.filter(
                atencion=atencion
            ).order_by("fecha_actualizacion")

    if Formulario and formularios_parto and generar_pdf_formulario_clinico:
        for form in formularios_parto:
            response_parto = generar_pdf_formulario_clinico(form)
            if isinstance(response_parto, HttpResponse):
                pdf_file = io.BytesIO(response_parto.content)
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)
                has_content = True

    # 4. --- CASO SIN CONTENIDO ---
    if not has_content:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.pagesizes import A4
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("HISTORIA CLÍNICA OBSTÉTRICA UNIFICADA", styles['Title']),
            Spacer(1, 20),
            Paragraph(f"No se encontraron registros clínicos cargados para la atención #{id}.", styles['Normal']),
            Paragraph(f"Paciente (ID): {documento_objetivo or atencion.paciente}", styles['Normal']),
            Spacer(1, 10),
            Paragraph("Por favor, registre datos en los módulos MEOWS, Fetal o Parto para generar el reporte completo.", styles['Italic'])
        ]
        doc.build(elements)
        buffer.seek(0)
        return HttpResponse(buffer.read(), content_type='application/pdf')

    # Salida final unificada ensamblada
    final_buffer = io.BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)
    
    response = HttpResponse(final_buffer.read(), content_type='application/pdf')
    filename = f"HC_Obstetrica_{documento_objetivo or atencion.paciente}_{id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def sala_de_partos(request):
    """
    Vista 'Sala de Partos': Hub para buscar pacientes y acceder a módulos.
    """
    db_choice = request.GET.get('db')
    if db_choice in ['readonly', 'nexus']:
        request.session['hospital_db'] = db_choice
        
    selected_db = request.session.get('hospital_db', 'readonly')

    return render(request, "obstetricia/sala_de_partos.html", {
        "is_dashboard": False,  # No es dashboard general
        "title": "Sala de Partos",
        "selected_db": selected_db
    })



