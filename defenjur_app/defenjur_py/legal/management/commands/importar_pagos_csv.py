"""
Importa pagos de sentencias judiciales desde CSV.

Uso:
    python manage.py importar_pagos_csv ruta/archivo.csv
    python manage.py importar_pagos_csv archivo.csv --dry-run
    python manage.py importar_pagos_csv archivo.csv --limpiar

Ignora id. Incluye imputacion_costo y fecha_registro si vienen en el CSV.
Si fecha_registro está vacía o no se puede interpretar, se usa la fecha/hora actual.
"""

import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.models import CharField
from django.utils import timezone

from legal.models import PagoSentenciaJudicial

IMPORT_CHAR_FIELDS = [
    'num_proceso',
    'despacho_tramitante',
    'medio_control',
    'demandante',
    'demandado',
    'valor_pagado',
    'estado',
    'tipo_pago',
    'abogado_responsable',
    'fecha_pago',
    'fecha_ejecutoria_sentencia',
    'imputacion_costo',
]

CSV_OPTIONAL_HEADERS = frozenset(IMPORT_CHAR_FIELDS) | {'id', 'fecha_registro'}


def _char_max_lengths():
    out = {}
    for field in PagoSentenciaJudicial._meta.concrete_fields:
        if isinstance(field, CharField):
            out[field.name] = field.max_length
    return out


def _clean(value):
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _parse_fecha_registro(raw):
    """Devuelve datetime con zona; si falla o viene vacío, ahora."""
    s = _clean(raw)
    if not s:
        return timezone.now()
    formats = (
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M',
        '%Y-%m-%d',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y',
        '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y',
    )
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            if timezone.is_naive(dt):
                return timezone.make_aware(dt)
            return dt
        except ValueError:
            continue
    return timezone.now()


def _row_to_instance(row: dict, char_limits: dict) -> PagoSentenciaJudicial:
    kwargs = {}
    for name in IMPORT_CHAR_FIELDS:
        val = _clean(row.get(name))
        if val is None:
            kwargs[name] = None
            continue
        lim = char_limits.get(name)
        if lim is not None and len(val) > lim:
            val = val[:lim]
        kwargs[name] = val
    kwargs['fecha_registro'] = _parse_fecha_registro(row.get('fecha_registro'))
    return PagoSentenciaJudicial(**kwargs)


class Command(BaseCommand):
    help = 'Importa PagoSentenciaJudicial desde CSV (UTF-8). Incluye imputacion_costo y fecha_registro.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta al archivo .csv')
        parser.add_argument('--dry-run', action='store_true', help='No escribe en la BD')
        parser.add_argument('--sep', type=str, default=None, help='Delimitador , o ;')
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina todos los pagos de sentencia antes de importar.',
        )

    def handle(self, *args, **options):
        path = Path(options['archivo']).expanduser().resolve()
        if not path.is_file():
            raise CommandError(f'No existe el archivo: {path}')

        sep = options['sep']
        if sep is not None and len(sep) != 1:
            raise CommandError('--sep debe ser un solo carácter')

        raw = path.read_bytes()
        encoding = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
        text = raw.decode(encoding, errors='replace')
        lines = text.splitlines()
        if not lines:
            raise CommandError('El archivo está vacío.')

        if sep is None:
            first = lines[0]
            sep = ';' if first.count(';') > first.count(',') else ','

        self.stdout.write(f'Delimitador: {repr(sep)} · codificación: {encoding}')

        reader = csv.DictReader(lines, delimiter=sep)
        if not reader.fieldnames:
            raise CommandError('No se pudieron leer encabezados.')

        reader.fieldnames = [
            h.strip().strip('\ufeff').lower() for h in reader.fieldnames if h is not None
        ]

        missing = [f for f in IMPORT_CHAR_FIELDS if f not in reader.fieldnames]
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    'Columnas no encontradas (quedarán vacías): ' + ', '.join(missing)
                )
            )

        if 'fecha_registro' not in reader.fieldnames:
            self.stdout.write(
                self.style.WARNING(
                    'El CSV no tiene columna fecha_registro; se usará la fecha/hora de importación en cada fila.'
                )
            )

        extra = [h for h in reader.fieldnames if h not in CSV_OPTIONAL_HEADERS]
        if extra:
            self.stdout.write(
                self.style.WARNING('Columnas del CSV no usadas: ' + ', '.join(extra))
            )

        char_limits = _char_max_lengths()
        batch: list[PagoSentenciaJudicial] = []
        batch_size = 300
        total = 0
        errors = 0
        truncated = 0

        if options['limpiar'] and not options['dry_run']:
            n = PagoSentenciaJudicial.objects.count()
            PagoSentenciaJudicial.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'[limpiar] Eliminados {n} registro(s).'))

        for i, row in enumerate(reader, start=2):
            norm = {k.strip().strip('\ufeff').lower(): v for k, v in row.items() if k}
            has_char = any(_clean(norm.get(f)) for f in IMPORT_CHAR_FIELDS)
            has_fecha_col = _clean(norm.get('fecha_registro'))
            if not has_char and not has_fecha_col:
                continue
            for name in IMPORT_CHAR_FIELDS:
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
                PagoSentenciaJudicial.objects.bulk_create(batch)
                batch.clear()

        if not options['dry_run'] and batch:
            PagoSentenciaJudicial.objects.bulk_create(batch)

        if truncated:
            self.stdout.write(
                self.style.WARNING(f'Aviso: {truncated} valor(es) truncados (límite CharField).')
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'[dry-run] Filas a importar: {total}. Errores: {errors}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Importados {total} pago(s) de sentencia. Errores: {errors}')
            )
