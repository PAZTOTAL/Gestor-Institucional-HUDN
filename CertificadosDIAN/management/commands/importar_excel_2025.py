import pandas as pd
import numpy as np
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from CertificadosDIAN.models import DatosCertificadoDIAN

class Command(BaseCommand):
    help = 'Importa datos de Certificados DIAN 2025 desde Excel'

    def handle(self, *args, **options):
        # Rutas posibles del archivo Excel
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'CertificadoIngresos2025.xlsm'),
            os.path.join(settings.BASE_DIR, 'media', 'certificados_dian', 'CertificadoIngresos2025.xlsm'),
            r'C:\Users\SISTEMAS\Documents\Gestor Institucional HUDN\CertificadoIngresos2025.xlsm'
        ]
        
        excel_path = None
        for path in possible_paths:
            if os.path.exists(path):
                excel_path = path
                break
        
        if not excel_path:
            self.stdout.write(self.style.ERROR(f'No se encontró el archivo Excel'))
            return

        self.stdout.write(self.style.SUCCESS(f'Leyendo archivo: {excel_path}'))

        try:
            df = pd.read_excel(excel_path, sheet_name='Hoja1', header=None, skiprows=2)
            total_rows = len(df)
            self.stdout.write(self.style.NOTICE(f'Filas detectadas en el Excel: {total_rows}'))
            
            if total_rows == 0:
                self.stdout.write(self.style.WARNING("No se detectaron filas de datos."))
                return

            contador_creados = 0
            contador_actualizados = 0

            log_file = os.path.join(settings.BASE_DIR, 'import_debug.log')
            with open(log_file, 'w') as f_log:
                f_log.write(f"Iniciando importacion. Filas: {total_rows}\n")

                for index, row in df.iterrows():
                    try:
                        cedula_raw = str(row[1])
                        cedula = cedula_raw.split('.')[0].strip()
                        
                        if not cedula or cedula == 'nan' or cedula == 'CEDULA':
                            continue
                        
                        # Mapeo de campos de texto
                        primer_apellido = str(row[106]).strip() if not pd.isna(row[106]) else ""
                        segundo_apellido = str(row[107]).strip() if not pd.isna(row[107]) else ""
                        primer_nombre = str(row[108]).strip() if not pd.isna(row[108]) else ""
                        otros_nombres = str(row[109]).strip() if not pd.isna(row[109]) else ""

                        # Mapeo de cajas (Valores numéricos)
                        def clean_val(val):
                            if pd.isna(val) or val == '':
                                return 0
                            try:
                                return float(val)
                            except:
                                return 0

                        cajas_data = {
                            'caja_36': clean_val(row[94]),
                            'caja_42': clean_val(row[95]),
                            'caja_46': clean_val(row[96]),
                            'caja_47': clean_val(row[97]),
                            'caja_49': clean_val(row[98]),
                            'caja_52': clean_val(row[99]),
                            'caja_53': clean_val(row[100]),
                            'caja_54': clean_val(row[101]),
                            'caja_56': clean_val(row[102]),
                            'caja_57': clean_val(row[103]),
                            'caja_59': clean_val(row[104]),
                            'caja_60': clean_val(row[105]),
                        }

                        obj, created = DatosCertificadoDIAN.objects.update_or_create(
                            anio_gravable=2025,
                            cedula=cedula,
                            defaults={
                                'primer_apellido': primer_apellido,
                                'segundo_apellido': segundo_apellido,
                                'primer_nombre': primer_nombre,
                                'otros_nombres': otros_nombres,
                                **cajas_data
                            }
                        )

                        if created:
                            contador_creados += 1
                        else:
                            contador_actualizados += 1

                        if (index + 1) % 100 == 0:
                            self.stdout.write(f'  Avance: {index + 1}/{total_rows}')
                            f_log.write(f"Procesadas {index + 1} filas...\n")

                    except Exception as e_row:
                        f_log.write(f"Error en fila {index}: {str(e_row)}\n")

            self.stdout.write(self.style.SUCCESS(f'Importación finalizada. Creados: {contador_creados}, Actualizados: {contador_actualizados}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
