"""
Importa peritajes desde CSV (export tipo legacy / Excel).

Uso:
    python manage.py importar_peritajes_csv C:\\TEMP\\4-peritajes_2025.csv
    python manage.py importar_peritajes_csv archivo.csv --dry-run
    python manage.py importar_peritajes_csv archivo.csv --sin-id   # ignora columna id (nuevos PK)

Por defecto usa la columna id con update_or_create (reimportar sin duplicar).
"""

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.models import CharField

from legal.models import Peritaje

IMPORT_CHAR_FIELDS = [
    'fecha_correo_electronico',
    'num_reparto',
    'fecha_reparto',
    'num_proceso',
    'entidad_remitente_requerimiento',
    'demandante',
    'demandado',
    'abogado_responsable',
    'fecha_asignar_perito',
    'perito_asignado',
    'pago_honorarios',
]

IMPORT_TEXT_FIELDS = ['asunto', 'observaciones']

CSV_KNOWN = frozenset(['id'] + IMPORT_CHAR_FIELDS + IMPORT_TEXT_FIELDS)


def _field_limits():
    lim = {}
    for f in Peritaje._meta.concrete_fields:
        if isinstance(f, CharField):
            lim[f.name] = f.max_length
    return lim


def _clean(value):
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


class Command(BaseCommand):
    help = 'Importa Peritaje desde CSV UTF-8 (multilínea entre comillas).'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta al .csv')
        parser.add_argument('--dry-run', action='store_true', help='No escribe en la BD')
        parser.add_argument('--sep', type=str, default=None, help='Delimitador , o ;')
        parser.add_argument(
            '--sin-id',
            action='store_true',
            help='No usar columna id: crea registros nuevos con PK autogenerada.',
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina todos los peritajes antes de importar.',
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

        missing = [f for f in IMPORT_CHAR_FIELDS + IMPORT_TEXT_FIELDS if f not in reader.fieldnames]
        if missing:
            raise CommandError('Faltan columnas en el CSV: ' + ', '.join(missing))

        extra = [h for h in reader.fieldnames if h not in CSV_KNOWN]
        if extra:
            self.stdout.write(self.style.WARNING('Columnas no usadas: ' + ', '.join(extra)))

        char_limits = _field_limits()
        use_id = not options['sin_id'] and 'id' in reader.fieldnames

        if options['limpiar'] and not options['dry_run']:
            n = Peritaje.objects.count()
            Peritaje.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'[limpiar] Eliminados {n} registro(s).'))

        created = 0
        updated = 0
        errors = 0
        truncated = 0

        for i, row in enumerate(reader, start=2):
            norm = {k.strip().strip('\ufeff').lower(): v for k, v in row.items() if k}
            defaults = {}
            for name in IMPORT_CHAR_FIELDS:
                val = _clean(norm.get(name))
                lim = char_limits.get(name)
                if val and lim and len(val) > lim:
                    val = val[:lim]
                    truncated += 1
                defaults[name] = val
            for name in IMPORT_TEXT_FIELDS:
                defaults[name] = _clean(norm.get(name))

            if not any(defaults.values()):
                continue

            if options['dry_run']:
                created += 1
                continue

            try:
                if use_id:
                    sid = _clean(norm.get('id'))
                    if not sid or not sid.isdigit():
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'Fila {i}: id inválido {sid!r}'))
                        continue
                    pk = int(sid)
                    obj, was_created = Peritaje.objects.update_or_create(pk=pk, defaults=defaults)
                    if was_created:
                        created += 1
                    else:
                        updated += 1
                else:
                    Peritaje.objects.create(**defaults)
                    created += 1
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'Fila {i}: {e}'))

        if truncated:
            self.stdout.write(
                self.style.WARNING(f'Aviso: {truncated} valor(es) CharField truncados.')
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'[dry-run] Filas con datos: {created}. Errores: {errors}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Listo: {created} creado(s), {updated} actualizado(s). Errores: {errors}'
                )
            )
