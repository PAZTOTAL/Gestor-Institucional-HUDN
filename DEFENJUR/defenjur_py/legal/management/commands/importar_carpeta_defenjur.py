"""
Importa todos los CSV de la carpeta DEFENJUR (legacy 2025 + exportaciones Excel 2026)
hacia los modelos del módulo legal.

Uso:
    python manage.py importar_carpeta_defenjur "C:\\ruta\\files_defenjur_2025"
    python manage.py importar_carpeta_defenjur --dry-run
    python manage.py importar_carpeta_defenjur --limpiar   # vacía tablas importables antes

Por defecto intenta la ruta del usuario si existe (solo Windows).
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db.models import CharField
from django.utils import timezone

from legal.models import (
    AccionTutela,
    DerechoPeticion,
    PagoSentenciaJudicial,
    Peritaje,
    ProcesoAdministrativoSancionatorio,
    ProcesoExtrajudicial,
    ProcesoJudicialActiva,
    ProcesoJudicialPasiva,
    ProcesoJudicialTerminado,
    RequerimientoEnteControl,
)

DEFAULT_CARPETA = Path(
    r"C:\Users\Daniel Ibarra\Desktop\Información Ing. Daniel Ibarra DEFENJUR"
    r"\files_defenjur_2025\files_defenjur_2025"
)

# Primera fila de algunos Excel es título, no encabezado.
_SKIP_TITLE_MARKERS = (
    "procesos judiciales",
    "derechos de petición",
    "derechos de peticion",
    "accione de tuetela",
    "acciones de tutela",
    "peritajes",
    "pagos de sentencias",
    "requerimientos entes",
)


def _clean(value):
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _clean_email(val):
    val = _clean(val)
    if not val:
        return None
    try:
        validate_email(val)
        return val
    except ValidationError:
        return None


def _char_limits(model):
    out = {}
    for f in model._meta.concrete_fields:
        if isinstance(f, CharField):
            out[f.name] = f.max_length
    return out


def _truncate_model_fields(model, data: dict) -> dict:
    lim = _char_limits(model)
    out = {}
    for k, v in data.items():
        if v is None:
            out[k] = None
            continue
        if k not in lim:
            out[k] = v
            continue
        m = lim[k]
        if m is not None and len(v) > m:
            out[k] = v[:m]
        else:
            out[k] = v
    return out


def _read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        enc = "utf-8-sig"
    else:
        enc = "utf-8"
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
        enc = "cp1252"
    return text, enc


def _detect_sep(line: str) -> str:
    return ";" if line.count(";") > line.count(",") else ","


def _header_line_index(lines: list[str], sep: str) -> int:
    if not lines:
        return 0
    first = lines[0]
    low = first.lower()
    if any(m in low for m in _SKIP_TITLE_MARKERS):
        return 1
    return 0


def _norm_header(h: str) -> str:
    if h is None:
        return ""
    return h.strip().strip("\ufeff").lower()


def _rows_from_csv(path: Path, sep: str | None = None):
    text, enc = _read_text(path)
    lines = text.splitlines()
    nonempty = [ln for ln in lines if ln.strip() != ""]
    if not nonempty:
        return [], ";", enc
    if sep is None:
        sep = _detect_sep(nonempty[0])
    start = _header_line_index(lines, sep)
    # StringIO conserva saltos dentro de campos entre comillas (CSV multilínea).
    body = "\n".join(lines[start:])
    reader = csv.DictReader(io.StringIO(body), delimiter=sep)
    if not reader.fieldnames:
        return [], sep, enc
    reader.fieldnames = [_norm_header(h) for h in reader.fieldnames if h is not None]
    rows = []
    for row in reader:
        norm = {_norm_header(k): v for k, v in row.items() if k}
        rows.append(norm)
    return rows, sep, enc


def _map_row(src: dict, mapping: dict[str, str]) -> dict:
    """mapping: csv_header_lower -> model_field (None = ignorar)."""
    out = {}
    for csv_key, field in mapping.items():
        if field is None:
            continue
        v = _clean(src.get(csv_key))
        if v is not None:
            out[field] = v
    return out


# --- Mapeos export Excel (encabezados en español, minúsculas tras _norm_header) ---
_MAP_JUD_SIMPLE = {
    "id": None,
    "n° proceso": "num_proceso",
    "nº proceso": "num_proceso",
    "demandante": "demandante",
    "demandado": "demandado",
    "apoderado": "apoderado",
    "despacho": "despacho_actual",
}

_MAP_DERECHOS_2026 = {
    "id": None,
    "n° reparto": "num_reparto",
    "nº reparto": "num_reparto",
    "fecha correo": "fecha_correo",
    "solicitante": "nombre_persona_solicitante",
    "peticionario": "peticionario",
    "causa": "causa_peticion",
    "abogado responsable": "abogado_responsable",
}

_MAP_TUTELA_2026 = {
    "id": None,
    "n° reparto": "num_reparto",
    "nº reparto": "num_reparto",
    "fecha correo": "fecha_correo",
    "fecha reparto": "fecha_reparto",
    "solicitante": "solicitante",
    "peticionario": "peticionario",
    "causa": "causa",
    "n° proceso": "num_proceso",
    "nº proceso": "num_proceso",
    "fecha llegada": "fecha_llegada",
    "despacho judicial": "despacho_judicial",
    "accionante": "accionante",
    "tipo ident. accionante": "tipo_identificacion_accionante",
    "ident. accionante": "identificacion_accionante",
    "accionado": "accionado",
    "abogado responsable": "abogado_responsable",
}

_MAP_PERITAJE_2026 = {
    "id": None,
    "n° proceso": "num_proceso",
    "nº proceso": "num_proceso",
    "fecha correo": "fecha_correo_electronico",
    "entidad requirente": "entidad_remitente_requerimiento",
    "demandante": "demandante",
    "demandado": "demandado",
    "abogado responsable": "abogado_responsable",
}

_MAP_PAGOS_2026 = {
    "id": None,
    "n° proceso": "num_proceso",
    "nº proceso": "num_proceso",
    "fecha pago": "fecha_pago",
    "despacho tramitante": "despacho_tramitante",
    "medio de control": "medio_control",
    "demandante": "demandante",
    "demandado": "demandado",
}

_MAP_REQ_ENTES_2026 = {
    "id": None,
    "n° reparto": "num_reparto",
    "nº reparto": "num_reparto",
    "n° proceso": "num_proceso",
    "nº proceso": "num_proceso",
    "fecha correo": "fecha_correo_electronico",
    "entidad": "entidad_remitente_requerimiento",
    "entidad remitente": "entidad_remitente_requerimiento",
    "entidad requirente": "entidad_remitente_requerimiento",
    "asunto": "asunto",
    "responsable": "abogado_responsable",
    "abogado responsable": "abogado_responsable",
}


def _tutela_fill_peticion_like(data: dict) -> None:
    """
    Si el CSV no trae columnas tipo petición, replica desde los campos judiciales habituales
    (misma lógica que el Excel actual de tutelas: fecha llegada ≈ fecha correo, etc.).
    """
    if not _clean(data.get("fecha_correo")) and _clean(data.get("fecha_llegada")):
        data["fecha_correo"] = data["fecha_llegada"]
    if not _clean(data.get("solicitante")) and _clean(data.get("accionante")):
        data["solicitante"] = data["accionante"]
    if not _clean(data.get("peticionario")) and _clean(data.get("accionado")):
        data["peticionario"] = data["accionado"]
    if not _clean(data.get("causa")):
        a = _clean(data.get("asunto_tutela"))
        o = _clean(data.get("objeto_tutela"))
        if a or o:
            data["causa"] = "\n\n".join(x for x in (a, o) if x)


def _pasiva_from_legacy_row(norm: dict) -> dict:
    def g(key):
        return _clean(norm.get(key))

    obs_parts = []
    for label, key in (
        ("Factor riesgo", "factor_riesgo"),
        ("Última actuación", "ultima_actuacion"),
        ("Fecha fallo 1ª inst.", "fecha_fallo_primera_instancia"),
        ("Link expediente", "link_expediente"),
    ):
        v = g(key)
        if v:
            obs_parts.append(f"{label}: {v}")
    base_obs = g("observaciones")
    if base_obs:
        obs_parts.insert(0, base_obs)

    hechos_chunks = [
        g("fortaleza_planteamientos_demanda"),
        g("material_probatorio_contra_entidad"),
        g("material_probatorio_excepciones_propuestas"),
        g("nivel_jurisprudencia"),
    ]
    hechos = "\n\n".join(h for h in hechos_chunks if h) or None

    return {
        "num_proceso": g("num_proceso"),
        "medio_control": g("medio_control"),
        "demandante": g("demandante"),
        "cc_demandante": g("cc_demandante"),
        "demandado": g("demandado"),
        "apoderado": g("apoderado"),
        "despacho_actual": g("despacho_actual"),
        "pretensiones": g("pretensiones"),
        "valor_pretension_inicial": g("valor_pretension_inicial"),
        "valor_provisionar": g("valor_probable_condena"),
        "fallo_sentencia": g("fallo_sentencia_primera_instancia"),
        "valor_fallo_sentencia": g("valor_fallo_sentencia"),
        "estado_actual": g("estado_actual"),
        "riesgo_perdida": g("riesgo_perdida"),
        "porcentaje_probabilidad_perdida": g("porcentaje_probabilidad_perdida"),
        "hechos_relevantes": hechos,
        "enfoque_defensa": g("enfoque_excepciones"),
        "calidad_entidad": g("calidad_entidad"),
        "hecho_generador": g("hecho_generador"),
        "observaciones": "\n".join(obs_parts) if obs_parts else None,
    }


def _fix_email_garbage(s: str | None) -> str | None:
    s = _clean(s)
    if not s:
        return None
    s = re.sub(r"\s+", " ", s)
    candidate = s.split()[0] if " " in s else s
    candidate = candidate.rstrip(".,;")
    return _clean_email(candidate) or _clean_email(s)


def _bulk_create_batches(model, instances: list, batch_size: int = 250):
    for i in range(0, len(instances), batch_size):
        model.objects.bulk_create(instances[i : i + batch_size])


class Command(BaseCommand):
    help = "Importa CSV de la carpeta DEFENJUR a los modelos del módulo legal."

    def add_arguments(self, parser):
        parser.add_argument(
            "carpeta",
            nargs="?",
            type=str,
            default=None,
            help="Ruta a la carpeta que contiene los .csv (opcional si existe la ruta por defecto).",
        )
        parser.add_argument("--dry-run", action="store_true", help="No escribe en la base de datos.")
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina registros de las tablas importables antes de cargar (no borra Usuario).",
        )
        parser.add_argument(
            "--solo",
            type=str,
            default="",
            help="Lista separada por comas: extrajudicial,activa,pasiva,terminados,peticiones,tutelas,"
            "peritajes,pagos,req_entes,pas_admin (si vacío, importa todo lo encontrado).",
        )

    def handle(self, *args, **options):
        carpeta_opt = options["carpeta"]
        if carpeta_opt:
            carpeta = Path(carpeta_opt).expanduser().resolve()
        elif DEFAULT_CARPETA.is_dir():
            carpeta = DEFAULT_CARPETA
            self.stdout.write(f"Usando carpeta por defecto: {carpeta}")
        else:
            raise CommandError(
                "Indica la ruta a la carpeta CSV o coloca los archivos en la ruta por defecto del proyecto."
            )

        if not carpeta.is_dir():
            raise CommandError(f"No es un directorio: {carpeta}")

        solo_raw = options["solo"].strip().lower()
        solo = {x.strip() for x in solo_raw.split(",") if x.strip()} if solo_raw else set()

        def want(key: str) -> bool:
            return not solo or key in solo

        dry = options["dry_run"]
        if options["limpiar"] and not dry:
            self.stdout.write(self.style.WARNING("[limpiar] Vaciando tablas importables..."))
            AccionTutela.objects.all().delete()
            DerechoPeticion.objects.all().delete()
            Peritaje.objects.all().delete()
            PagoSentenciaJudicial.objects.all().delete()
            ProcesoJudicialTerminado.objects.all().delete()
            ProcesoJudicialPasiva.objects.all().delete()
            ProcesoJudicialActiva.objects.all().delete()
            ProcesoExtrajudicial.objects.all().delete()
            ProcesoAdministrativoSancionatorio.objects.all().delete()
            RequerimientoEnteControl.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("[limpiar] Listo."))

        files = {p.name.lower(): p for p in carpeta.iterdir() if p.suffix.lower() == ".csv"}
        total_imported = 0

        def run_extrajudicial():
            nonlocal total_imported
            p = files.get("procs_extrajudiciales_2025.csv")
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: procs_extrajudiciales_2025.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[extrajudicial] {p.name} · {sep!r} · {enc}")
            batch = []
            n = 0
            for norm in rows:
                data = {
                    "demandante": _clean(norm.get("demandante")),
                    "demandado": _clean(norm.get("demandado")),
                    "apoderado": _clean(norm.get("apoderado")),
                    "medio_control": _clean(norm.get("medio_control")) or "",
                    "despacho_conocimiento": _clean(norm.get("despacho_conocimiento")) or "",
                    "estado": _clean(norm.get("estado")) or "",
                    "clasificacion": _clean(norm.get("clasificacion")),
                }
                if not any([data["demandante"], data["demandado"], data["medio_control"]]):
                    continue
                data = _truncate_model_fields(ProcesoExtrajudicial, data)
                n += 1
                if not dry:
                    batch.append(ProcesoExtrajudicial(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(ProcesoExtrajudicial, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(ProcesoExtrajudicial, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} fila(s) extrajudicial(es)."))
            total_imported += n

        def run_pas_admin():
            nonlocal total_imported
            p = files.get("procs_adm_sanc_2025.csv")
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: procs_adm_sanc_2025.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[pas_admin] {p.name} · {sep!r} · {enc}")
            fields = [f.name for f in ProcesoAdministrativoSancionatorio._meta.concrete_fields if f.name not in ("id", "fecha_registro")]
            batch = []
            n = 0
            for norm in rows:
                data = {fn: _clean(norm.get(fn)) for fn in fields}
                if not any(data.values()):
                    continue
                data = _truncate_model_fields(ProcesoAdministrativoSancionatorio, data)
                n += 1
                if not dry:
                    batch.append(ProcesoAdministrativoSancionatorio(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(ProcesoAdministrativoSancionatorio, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(ProcesoAdministrativoSancionatorio, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} proceso(s) administrativo(s) sancionatorio(s)."))
            total_imported += n

        def run_req_2025():
            nonlocal total_imported
            p = files.get("req_entes_control_2025.csv")
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: req_entes_control_2025.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[req_entes 2025] {p.name} · {sep!r} · {enc}")
            fields = [f.name for f in RequerimientoEnteControl._meta.concrete_fields if f.name not in ("id", "fecha_registro")]
            batch = []
            n = 0
            for norm in rows:
                data = {fn: _clean(norm.get(fn)) for fn in fields}
                if fn_correo := data.get("correo"):
                    data["correo"] = _fix_email_garbage(fn_correo)
                if not any(v for k, v in data.items() if k != "correo") and not data.get("correo"):
                    continue
                data = _truncate_model_fields(RequerimientoEnteControl, data)
                n += 1
                if not dry:
                    batch.append(RequerimientoEnteControl(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(RequerimientoEnteControl, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(RequerimientoEnteControl, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} requerimiento(s) (2025)."))
            total_imported += n

        def run_pasiva_legacy(name: str):
            nonlocal total_imported
            key = name.lower()
            p = files.get(key)
            if not p:
                self.stdout.write(self.style.WARNING(f"Omiso: {name} no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[pasiva legacy] {p.name} · {sep!r} · {enc}")
            n = 0
            for norm in rows:
                data = _pasiva_from_legacy_row(norm)
                if not data.get("num_proceso") and not data.get("demandante"):
                    continue
                data = _truncate_model_fields(ProcesoJudicialPasiva, data)
                n += 1
                if dry:
                    continue
                np = _clean(data.get("num_proceso")) or ""
                mc = _clean(data.get("medio_control")) or ""
                ProcesoJudicialPasiva.objects.update_or_create(
                    num_proceso=np,
                    medio_control=mc,
                    defaults=data,
                )
            self.stdout.write(self.style.SUCCESS(f"  -> {n} fila(s) pasivas (legacy)."))
            total_imported += n

        def run_jud_simple(filename: str, model, label: str, only_map: dict):
            nonlocal total_imported
            key = filename.lower()
            p = files.get(key)
            if not p:
                self.stdout.write(self.style.WARNING(f"Omiso: {filename} no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[{label}] {p.name} · {sep!r} · {enc}")
            batch = []
            n = 0
            for norm in rows:
                data = _map_row(norm, only_map)
                if not any(data.values()):
                    continue
                data = _truncate_model_fields(model, data)
                n += 1
                if not dry:
                    batch.append(model(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(model, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(model, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} registro(s) {label}."))
            total_imported += n

        def run_derechos_2026():
            nonlocal total_imported
            key = "derechos de petición-2026.csv"
            p = files.get(key)
            if not p:
                alt = "derechos de peticion-2026.csv"
                p = files.get(alt)
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: Derechos de Petición-2026.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[peticiones] {p.name} · {sep!r} · {enc}")
            all_fields = [f.name for f in DerechoPeticion._meta.concrete_fields if f.name != "id"]
            batch = []
            n = 0
            for norm in rows:
                data = {f: None for f in all_fields}
                mapped = _map_row(norm, _MAP_DERECHOS_2026)
                data.update(mapped)
                if data.get("correo_remitente_peticion"):
                    data["correo_remitente_peticion"] = _clean_email(data["correo_remitente_peticion"])
                if not any(_clean(data.get(f)) for f in all_fields):
                    continue
                data = _truncate_model_fields(DerechoPeticion, data)
                n += 1
                if not dry:
                    batch.append(DerechoPeticion(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(DerechoPeticion, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(DerechoPeticion, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} derecho(s) de petición."))
            total_imported += n

        def run_tutelas_2026():
            nonlocal total_imported
            key = "accione de tuetela-2026.csv"
            p = files.get(key)
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: Accione de tuetela-2026.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[tutelas] {p.name} · {sep!r} · {enc}")
            tutela_fields = [f.name for f in AccionTutela._meta.concrete_fields if f.name != "id"]
            batch = []
            n = 0
            for norm in rows:
                data = {f: None for f in tutela_fields}
                data.update(_map_row(norm, _MAP_TUTELA_2026))
                _tutela_fill_peticion_like(data)
                if not any(_clean(data.get(f)) for f in tutela_fields):
                    continue
                data = _truncate_model_fields(AccionTutela, data)
                n += 1
                if not dry:
                    batch.append(AccionTutela(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(AccionTutela, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(AccionTutela, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} tutela(s)."))
            total_imported += n

        def run_peritajes_2026():
            nonlocal total_imported
            key = "peritajes-2026.csv"
            p = files.get(key)
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: Peritajes-2026.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[peritajes] {p.name} · {sep!r} · {enc}")
            all_fields = [f.name for f in Peritaje._meta.concrete_fields if f.name not in ("id", "fecha_registro")]
            batch = []
            n = 0
            for norm in rows:
                data = {f: None for f in all_fields}
                data.update(_map_row(norm, _MAP_PERITAJE_2026))
                if not any(_clean(data.get(f)) for f in all_fields):
                    continue
                data = _truncate_model_fields(Peritaje, data)
                n += 1
                if not dry:
                    batch.append(Peritaje(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(Peritaje, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(Peritaje, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} peritaje(s)."))
            total_imported += n

        def run_pagos_2026():
            nonlocal total_imported
            key = "pagos de sentencias judiciales-2026.csv"
            p = files.get(key)
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: Pagos de Sentencias Judiciales-2026.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[pagos] {p.name} · {sep!r} · {enc}")
            char_names = [
                "num_proceso",
                "despacho_tramitante",
                "medio_control",
                "demandante",
                "demandado",
                "valor_pagado",
                "estado",
                "tipo_pago",
                "abogado_responsable",
                "fecha_pago",
                "fecha_ejecutoria_sentencia",
                "imputacion_costo",
            ]
            lim = _char_limits(PagoSentenciaJudicial)
            batch = []
            n = 0
            for norm in rows:
                mapped = _map_row(norm, _MAP_PAGOS_2026)
                data = {k: None for k in char_names}
                data.update(mapped)
                data["fecha_registro"] = timezone.now()
                if not any(_clean(data.get(k)) for k in char_names):
                    continue
                for name in char_names:
                    val = _clean(data.get(name))
                    if val and lim.get(name) and len(val) > lim[name]:
                        val = val[: lim[name]]
                    data[name] = val
                n += 1
                if not dry:
                    batch.append(PagoSentenciaJudicial(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(PagoSentenciaJudicial, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(PagoSentenciaJudicial, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} pago(s) de sentencia."))
            total_imported += n

        def run_req_2026():
            nonlocal total_imported
            key = "requerimientos entes de control-2026.csv"
            p = files.get(key)
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: Requerimientos Entes de Control-2026.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[req_entes 2026] {p.name} · {sep!r} · {enc}")
            all_fields = [f.name for f in RequerimientoEnteControl._meta.concrete_fields if f.name not in ("id", "fecha_registro")]
            batch = []
            n = 0
            for norm in rows:
                data = {f: None for f in all_fields}
                data.update(_map_row(norm, _MAP_REQ_ENTES_2026))
                if data.get("correo"):
                    data["correo"] = _fix_email_garbage(data["correo"])
                if not any(_clean(data.get(f)) for f in all_fields):
                    continue
                data = _truncate_model_fields(RequerimientoEnteControl, data)
                n += 1
                if not dry:
                    batch.append(RequerimientoEnteControl(**data))
                    if len(batch) >= 250:
                        _bulk_create_batches(RequerimientoEnteControl, batch)
                        batch.clear()
            if not dry and batch:
                _bulk_create_batches(RequerimientoEnteControl, batch)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} requerimiento(s) (2026)."))
            total_imported += n

        def run_pasiva_excel():
            """Excel trae pocas columnas: fusiona en el registro pasivo con mismo N° proceso (evita duplicar legacy)."""
            nonlocal total_imported
            key = "procesos judiciales por pasiva-2026.csv"
            p = files.get(key)
            if not p:
                self.stdout.write(self.style.WARNING("Omiso: Procesos Judiciales por Pasiva-2026.csv no encontrado."))
                return
            rows, sep, enc = _rows_from_csv(p)
            self.stdout.write(f"\n[pasiva Excel] {p.name} · {sep!r} · {enc}")
            n = 0
            for norm in rows:
                data = _map_row(norm, _MAP_JUD_SIMPLE)
                if not data.get("num_proceso") and not data.get("demandante"):
                    continue
                data = _truncate_model_fields(ProcesoJudicialPasiva, data)
                n += 1
                if dry:
                    continue
                np = _clean(data.get("num_proceso")) or ""
                obj = (
                    ProcesoJudicialPasiva.objects.filter(num_proceso=np)
                    .order_by("-id")
                    .first()
                )
                if obj:
                    for k, v in data.items():
                        if v is None or (isinstance(v, str) and not v.strip()):
                            continue
                        cur = getattr(obj, k)
                        if cur is None or (isinstance(cur, str) and not str(cur).strip()):
                            setattr(obj, k, v)
                    obj.save()
                else:
                    ProcesoJudicialPasiva.objects.create(**data)
            self.stdout.write(self.style.SUCCESS(f"  -> {n} fila(s) pasivas (Excel)."))
            total_imported += n

        if want("extrajudicial"):
            run_extrajudicial()
        if want("pas_admin"):
            run_pas_admin()
        if want("req_entes"):
            run_req_2025()
        if want("pasiva"):
            run_pasiva_legacy("procs_jud_pasiva_2025.csv")
            run_pasiva_legacy("v2procs_judiciales_pasiva_2025.csv")
            run_pasiva_excel()
        if want("activa"):
            run_jud_simple(
                "Procesos Judiciales por Activa-2026.csv",
                ProcesoJudicialActiva,
                "activa",
                {**_MAP_JUD_SIMPLE, "despacho": "despacho_actual"},
            )
        if want("terminados"):
            run_jud_simple(
                "Procesos Judiciales Terminados-2026.csv",
                ProcesoJudicialTerminado,
                "terminados",
                {**_MAP_JUD_SIMPLE, "despacho": "despacho_actual"},
            )
        if want("peticiones"):
            run_derechos_2026()
        if want("tutelas"):
            run_tutelas_2026()
        if want("peritajes"):
            run_peritajes_2026()
        if want("pagos"):
            run_pagos_2026()
        if want("req_entes"):
            run_req_2026()

        msg = f"\nTotal filas procesadas (conteo por módulo): {total_imported}"
        if dry:
            self.stdout.write(self.style.SUCCESS(msg + " [dry-run, sin escritura]"))
        else:
            self.stdout.write(self.style.SUCCESS(msg + " · Importación finalizada."))
