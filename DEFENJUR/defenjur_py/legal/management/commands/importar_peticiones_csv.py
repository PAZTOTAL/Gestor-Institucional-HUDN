"""
Importa derechos de petición desde CSV (Excel).

Uso:
    python manage.py importar_peticiones_csv ruta/archivo.csv
    python manage.py importar_peticiones_csv archivo.csv --dry-run
    python manage.py importar_peticiones_csv archivo.csv --limpiar

Ignora la columna id. Encabezados en minúsculas (p. ej. correo_remitente_peticion).
"""

import csv
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db.models import CharField

from legal.models import DerechoPeticion

IMPORT_FIELDS = [
    'fecha_correo',
    'correo_remitente_peticion',
    'num_reparto',
    'fecha_reparto',
    'num_rad_interno',
    'fecha_remitente_peticion',
    'nombre_persona_solicitante',
    'cedula_persona_solicitante',
    'peticionario_int_ext',
    'peticionario',
    'causa_peticion',
    'abogado_responsable',
    'modalidad_peticion',
    'tramite_impartido',
    'tiempo_area_remitir_informacion',
    'area_remitir_informacion',
    'termino_dar_tramite',
    'fecha_respuesta_peticion',
    'num_rad_arch_central',
    'observaciones',
]


def _char_max_lengths():
    out = {}
    for field in DerechoPeticion._meta.concrete_fields:
        if isinstance(field, CharField):
            out[field.name] = field.max_length
    return out


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


def _row_to_instance(row: dict, char_limits: dict) -> DerechoPeticion:
    kwargs = {}
    for name in IMPORT_FIELDS:
        if name == 'correo_remitente_peticion':
            kwargs[name] = _clean_email(row.get(name))
            continue
        raw = row.get(name)
        val = _clean(raw)
        if val is None:
            kwargs[name] = None
            continue
        lim = char_limits.get(name)
        if lim is not None and len(val) > lim:
            val = val[:lim]
        kwargs[name] = val
    return DerechoPeticion(**kwargs)


class Command(BaseCommand):
    help = 'Importa DerechoPeticion desde CSV (UTF-8). Ignora id. Emails inválidos → vacío.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta al archivo .csv')
        parser.add_argument('--dry-run', action='store_true', help='No escribe en la BD')
        parser.add_argument('--sep', type=str, default=None, help='Delimitador , o ;')
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina todos los derechos de petición antes de importar.',
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

        missing = [f for f in IMPORT_FIELDS if f not in reader.fieldnames]
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    'Columnas no encontradas (quedarán vacías): ' + ', '.join(missing)
                )
            )

        char_limits = _char_max_lengths()
        batch: list[DerechoPeticion] = []
        batch_size = 300
        total = 0
        errors = 0
        truncated = 0
        email_dropped = 0

        if options['limpiar'] and not options['dry_run']:
            n = DerechoPeticion.objects.count()
            DerechoPeticion.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'[limpiar] Eliminados {n} registro(s).'))

        for i, row in enumerate(reader, start=2):
            norm = {k.strip().strip('\ufeff').lower(): v for k, v in row.items() if k}
            raw_mail = _clean(norm.get('correo_remitente_peticion'))
            if raw_mail and _clean_email(raw_mail) is None:
                email_dropped += 1
            if not any(_clean(norm.get(f)) for f in IMPORT_FIELDS):
                continue
            for name in IMPORT_FIELDS:
                if name == 'correo_remitente_peticion':
                    continue
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
                DerechoPeticion.objects.bulk_create(batch)
                batch.clear()

        if not options['dry_run'] and batch:
            DerechoPeticion.objects.bulk_create(batch)

        if truncated:
            self.stdout.write(
                self.style.WARNING(f'Aviso: {truncated} valor(es) truncados (límite CharField).')
            )
        if email_dropped:
            self.stdout.write(
                self.style.WARNING(
                    f'Aviso: {email_dropped} correo(s) con formato inválido se dejaron vacíos.'
                )
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[dry-run] Filas a importar: {total}. Errores: {errors}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Importados {total} derecho(s) de petición. Errores: {errors}'
                )
            )
