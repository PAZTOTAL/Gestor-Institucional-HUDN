"""
Comando: python manage.py importar_personal

Lee horas_extras/data/personal.xlsx y popula las tablas
AreaRecargos y TrabajadorRecargos en GestorInstitucional.

Opciones:
  --limpiar   Elimina todos los trabajadores y áreas antes de importar
  --dry-run   Solo muestra qué haría sin escribir nada
"""

import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from horas_extras.models import AreaRecargos, TrabajadorRecargos

EXCEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'data', 'personal.xlsx'
)

VINCULACION_MAP = {
    'PERMANENTE': 'permanente',
    'TEMPORAL':   'temporal',
    'OPS':        'ops',
}


class Command(BaseCommand):
    help = 'Importa el personal desde horas_extras/data/personal.xlsx a TrabajadorRecargos'

    def add_arguments(self, parser):
        parser.add_argument('--limpiar', action='store_true',
                            help='Elimina todos los registros existentes antes de importar')
        parser.add_argument('--dry-run', action='store_true',
                            help='Muestra qué haría sin escribir en la BD')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limpiar = options['limpiar']

        # ── Cargar Excel ──────────────────────────────────────────────────────
        ruta = os.path.normpath(EXCEL_PATH)
        if not os.path.exists(ruta):
            raise CommandError(f'No se encontró el archivo: {ruta}')

        df = pd.read_excel(ruta)
        df.columns = [c.upper().strip() for c in df.columns]

        columnas_req = {'CEDULA', 'NOMBRE', 'VINCULACION', 'CARGO', 'AREA'}
        faltantes = columnas_req - set(df.columns)
        if faltantes:
            raise CommandError(f'Columnas faltantes en el Excel: {faltantes}')

        # Limpiar valores
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        df = df[df['CEDULA'].notna() & (df['CEDULA'] != '') & (df['CEDULA'] != 'nan')]

        self.stdout.write(f'Filas a procesar: {len(df)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('--- MODO DRY-RUN (no se escribe nada) ---'))

        # ── Limpiar si se pidió ───────────────────────────────────────────────
        if limpiar and not dry_run:
            total_t = TrabajadorRecargos.objects.count()
            total_a = AreaRecargos.objects.count()
            TrabajadorRecargos.objects.all().delete()
            AreaRecargos.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'Eliminados {total_t} trabajadores y {total_a} áreas.'
            ))

        # ── Crear/obtener áreas únicas ────────────────────────────────────────
        areas_unicas = df['AREA'].dropna().unique()
        areas_cache = {}
        nuevas_areas = 0

        for nombre_area in areas_unicas:
            if not nombre_area or nombre_area == 'nan':
                continue
            if not dry_run:
                area, creada = AreaRecargos.objects.get_or_create(
                    nombre=nombre_area.title(),
                    defaults={'descripcion': ''}
                )
                areas_cache[nombre_area] = area
                if creada:
                    nuevas_areas += 1
            else:
                areas_cache[nombre_area] = None

        self.stdout.write(f'Áreas nuevas creadas: {nuevas_areas}')

        # ── Importar trabajadores ─────────────────────────────────────────────
        creados = 0
        actualizados = 0
        omitidos = 0

        for _, row in df.iterrows():
            cedula      = str(row['CEDULA']).strip()
            nombre      = str(row['NOMBRE']).strip().title()
            vinculacion = str(row['VINCULACION']).strip().upper()
            cargo       = str(row['CARGO']).strip().title()
            area_nombre = str(row['AREA']).strip()

            tipo = VINCULACION_MAP.get(vinculacion, 'temporal')
            area = areas_cache.get(area_nombre)

            if not cedula or cedula == 'nan':
                omitidos += 1
                continue

            if dry_run:
                self.stdout.write(f'  [{tipo[:3].upper()}] {cedula} - {nombre} → {area_nombre}')
                creados += 1
                continue

            if area is None:
                area, _ = AreaRecargos.objects.get_or_create(
                    nombre=area_nombre.title(),
                    defaults={'descripcion': ''}
                )
                areas_cache[area_nombre] = area

            trabajador, creado = TrabajadorRecargos.objects.update_or_create(
                documento=cedula,
                defaults={
                    'nombre': nombre,
                    'cargo':  cargo,
                    'area':   area,
                    'tipo':   tipo,
                }
            )
            if creado:
                creados += 1
            else:
                actualizados += 1

        # ── Resumen ───────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f'\nImportación completada:'
            f'\n  Creados:     {creados}'
            f'\n  Actualizados:{actualizados}'
            f'\n  Omitidos:    {omitidos}'
        ))
