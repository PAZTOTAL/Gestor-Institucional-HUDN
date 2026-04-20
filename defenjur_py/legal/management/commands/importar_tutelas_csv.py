"""
Importa acciones de tutela desde un CSV exportado de Excel.

Uso:
    python manage.py importar_tutelas_csv ruta/al/archivo.csv
    python manage.py importar_tutelas_csv archivo.csv --dry-run
    python manage.py importar_tutelas_csv archivo.csv --sep ";"
    python manage.py importar_tutelas_csv archivo.csv --limpiar   # borra todas las tutelas antes

La columna "id" del Excel se ignora (Django asigna PK nuevo).
Encabezados esperados (pueden faltar columnas opcionales):
    fecha_correo, num_reparto, fecha_reparto, solicitante, peticionario, causa,
    fecha_llegada, num_proceso, despacho_judicial,
    area_responsable, accionante, tipo_identificacion_accionante, identificacion_accionante,
    accionado, vinculados, objeto_tutela, asunto_tutela, abogado_responsable,
    tipo_tramite, termino_dar_tramite, observaciones
"""

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.models import CharField

from legal.models import AccionTutela

# Campos importables desde CSV (excluye id y el resto de campos del modelo quedan vacíos)
IMPORT_FIELDS = [
    'fecha_correo',
    'num_reparto',
    'fecha_reparto',
    'solicitante',
    'peticionario',
    'causa',
    'fecha_llegada',
    'num_proceso',
    'despacho_judicial',
    'area_responsable',
    'accionante',
    'tipo_identificacion_accionante',
    'identificacion_accionante',
    'accionado',
    'vinculados',
    'objeto_tutela',
    'asunto_tutela',
    'abogado_responsable',
    'tipo_tramite',
    'termino_dar_tramite',
    'observaciones',
]


def _char_max_lengths():
    out = {}
    for field in AccionTutela._meta.concrete_fields:
        if isinstance(field, CharField):
            out[field.name] = field.max_length
    return out


def _clean(value):
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _row_to_instance(row: dict, char_limits: dict) -> AccionTutela:
    kwargs = {}
    for name in IMPORT_FIELDS:
        raw = row.get(name)
        val = _clean(raw)
        if val is None:
            kwargs[name] = None
            continue
        lim = char_limits.get(name)
        if lim is not None and len(val) > lim:
            val = val[:lim]
        kwargs[name] = val
    return AccionTutela(**kwargs)


class Command(BaseCommand):
    help = 'Importa AccionTutela desde CSV (UTF-8). Ignora la columna id del Excel.'

    def add_arguments(self, parser):
        parser.add_argument(
            'archivo',
            type=str,
            help='Ruta al archivo .csv',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo valida y cuenta filas; no escribe en la base de datos.',
        )
        parser.add_argument(
            '--sep',
            type=str,
            default=None,
            help='Delimitador: , o ; (por defecto se intenta detectar)',
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina todas las tutelas existentes antes de importar.',
        )

    def handle(self, *args, **options):
        path = Path(options['archivo']).expanduser().resolve()
        if not path.is_file():
            raise CommandError(f'No existe el archivo: {path}')

        sep = options['sep']
        if sep is not None and len(sep) != 1:
            raise CommandError('--sep debe ser un solo carácter (por ejemplo , o ;)')

        raw = path.read_bytes()
        if raw.startswith(b'\xef\xbb\xbf'):
            encoding = 'utf-8-sig'
        else:
            encoding = 'utf-8'

        text = raw.decode(encoding, errors='replace')
        lines = text.splitlines()
        if not lines:
            raise CommandError('El archivo está vacío.')

        if sep is None:
            first = lines[0]
            n_comma = first.count(',')
            n_semi = first.count(';')
            sep = ';' if n_semi > n_comma else ','

        self.stdout.write(f'Delimitador: {repr(sep)} · codificación: {encoding}')

        reader = csv.DictReader(lines, delimiter=sep)
        if not reader.fieldnames:
            raise CommandError('No se pudieron leer encabezados del CSV.')

        # Minúsculas: Excel a veces exporta "Observaciones" y no coincidía con el campo observaciones.
        headers = [h.strip().strip('\ufeff').lower() for h in reader.fieldnames if h is not None]
        reader.fieldnames = headers

        missing = [f for f in IMPORT_FIELDS if f not in headers]
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    f'Columnas no encontradas en el CSV (se guardarán vacías): {", ".join(missing)}'
                )
            )

        char_limits = _char_max_lengths()
        batch: list[AccionTutela] = []
        batch_size = 300
        total = 0
        errors = 0
        truncated = 0

        if options['limpiar'] and not options['dry_run']:
            n = AccionTutela.objects.count()
            AccionTutela.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'[limpiar] Eliminadas {n} tutela(s) existentes.'))

        for i, row in enumerate(reader, start=2):
            norm = { (k.strip().strip('\ufeff').lower() if k else k): v for k, v in row.items() if k }
            if not any(_clean(norm.get(f)) for f in IMPORT_FIELDS):
                continue
            for name in IMPORT_FIELDS:
                val = _clean(norm.get(name))
                lim = char_limits.get(name)
                if val and lim and len(val) > lim:
                    truncated += 1
            try:
                obj = _row_to_instance(norm, char_limits)
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'Fila {i}: {e}'))
                continue
            total += 1
            if options['dry_run']:
                continue
            batch.append(obj)
            if len(batch) >= batch_size:
                AccionTutela.objects.bulk_create(batch)
                batch.clear()

        if not options['dry_run'] and batch:
            AccionTutela.objects.bulk_create(batch)

        if truncated:
            self.stdout.write(
                self.style.WARNING(
                    f'Aviso: {truncated} valor(es) truncados por límite de caracteres del modelo.'
                )
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[dry-run] Filas válidas a importar: {total} (sin escribir en BD). Errores: {errors}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Importadas {total} acción(es) de tutela. Errores de fila: {errors}'
                )
            )
