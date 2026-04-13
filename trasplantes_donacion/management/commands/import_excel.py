import pandas as pd
from django.core.management.base import BaseCommand
from trasplantes_donacion.models import PacienteNeurocritico
from django.utils import timezone
import math

class Command(BaseCommand):
    help = 'Importa datos desde el Excel de Neurocríticos'

    def handle(self, *args, **options):
        file_path = r'H:\HUDN\BASE DATOS NEUROCRITICOS ENERO.xlsx'
        try:
            df = pd.read_excel(file_path)
            
            # Limpiar datos previos (opcional o sync por documento)
            # PacienteNeurocritico.objects.all().delete()
            
            count = 0
            for index, row in df.iterrows():
                # Saltar filas sin documento
                doc = str(row.get('NUMERO DE DOCUMENTO ', '')).strip()
                if not doc or doc == 'nan':
                    continue
                
                def clean_val(val, default=None):
                    if pd.isna(val) or str(val) == 'nan':
                        return default
                    return val

                def clean_int(val):
                    try:
                        return int(float(val))
                    except:
                        return None

                def clean_date(val):
                    if pd.isna(val) or str(val) == 'nan':
                        return None
                    try:
                        return pd.to_datetime(val)
                    except:
                        return None

                # Mapeo de campos
                paciente, created = PacienteNeurocritico.objects.update_or_create(
                    numero_documento=doc,
                    defaults={
                        'item': clean_int(row.get('ITEM')),
                        'fecha_identificacion': clean_date(row.get('FECHA DE IDENTIFICACION')),
                        'busqueda_activa': clean_val(row.get('BUSQUEDA ACTIVA')),
                        'busqueda_pasiva': clean_val(row.get('BUSQUEDA PASIVA ')),
                        'servicio': clean_val(row.get('SERVICIO')),
                        'paciente_intubado': clean_val(row.get('PACIENTE INTUBADO (SI/NO)')),
                        'tipo_identificacion': clean_val(row.get('TIPO DE IDENTIFICACION')),
                        'primer_nombre': clean_val(row.get('PRIMER NOMBRE')),
                        'segundo_nombre': clean_val(row.get('SEGUNDO NOMBRE')),
                        'primer_apellido': clean_val(row.get('PRIMER APELLIDO')),
                        'segundo_apellido': clean_val(row.get('SEGUNDO APELLIDO')),
                        'fecha_nacimiento': clean_date(row.get('FECHA DE NACIMIENTO')),
                        'sexo': clean_val(row.get('SEXO')),
                        'edad': clean_int(row.get('EDAD')),
                        'ocupacion': clean_val(row.get('OCUPACION')),
                        'etnia': clean_val(row.get('ETNIA ')),
                        'municipio_residencia': clean_val(row.get('MUNICIPIO DE RESIDENCIA ')),
                        'eapb': clean_val(row.get('EAPB')),
                        'fecha_ingreso': clean_date(row.get('FECHA DE INGRESO')),
                        'glasgow_ingreso': clean_int(row.get('GLASGOW DE INGRESO ')),
                        'codigo_cie10': clean_val(row.get('CODIGO CIE10')),
                        'diagnostico': clean_val(row.get('DIAGNOSTICO')),
                        'paciente_alertado': clean_val(row.get('PACIENTE ALERTADO SI /NO ')),
                        'fecha_hora_alerta_crt': clean_date(row.get('FECHA Y HORA DE ALERTA A CRT')),
                        'causa_no_alerta': clean_val(row.get('CAUSA DE NO ALERTA ')),
                        'voluntades_anticipadas': clean_val(row.get('CODIGO DE VOLUNTADES ANTICIPIDAS ')),
                        'dx_muerte_encefalica': clean_val(row.get('DX DE MUERTE ENCEFALICA (SI/NO)')),
                        'fecha_diagnostico_me_hora': clean_date(row.get('FECHA DE DIAGNOSTICO DE MUERTE ENCEFALICA Y HORA ')),
                        'paciente_legalizado': clean_val(row.get('PACIENTE LEGALIZADO SI/NO')),
                        'causa_no_legalizacion': clean_val(row.get('CAUSA DE NO LEGALIZACION')),
                        'fecha_legalizacion': clean_date(row.get(' FECHA DE LEGALIZACION')),
                        'donante_efectivo': clean_val(row.get('DONANTE EFECTIVO SI/NO')),
                        'causa_no_donante_efectivo': clean_val(row.get('CAUSA DE NO SER DONANTE EFECTIVO ')),
                        'estado_vital_egreso': clean_val(row.get('ESTADO VITAL EGRESO ')),
                        'fecha_egreso': clean_date(row.get('FECHA DE EGRESO ')),
                        'organos_recatados': clean_val(row.get('ORGANOS RECATADOS ')),
                        'medico_alerta': clean_val(row.get('MEDICO QUE ALERTA ')),
                        'medico_no_alerta': clean_val(row.get('MEDICO QUE NO ALERTA ')),
                        'observaciones': clean_val(row.get('OBSERVACIONES ')),
                    }
                )
                count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Sincronización completa: {count} registros procesados.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al procesar el Excel: {e}'))
