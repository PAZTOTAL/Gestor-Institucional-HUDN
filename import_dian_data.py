import os
import django
import pandas as pd
import numpy as np

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from CertificadosDIAN.models import DatosCertificadoDIAN

def fix_encoding(text):
    if not isinstance(text, str):
        return text
    # \ufffd is the unicode replacement character
    return text.replace('\ufffd', 'Ñ').strip()

def import_dian_data():
    file_path = 'CertificadoIngresos2025.xlsm'
    sheet_name = 'Hoja1'
    
    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='openpyxl')
    
    data_df = df.iloc[2:]
    
    count = 0
    for index, row in data_df.iterrows():
        cedula = str(row[1]).strip()
        if not cedula or cedula == 'nan' or cedula == 'None' or cedula == 'CEDULA':
            continue
            
        try:
            if cedula.endswith('.0'):
                cedula = cedula[:-2]
            
            p_apellido = fix_encoding(str(row[106])) if not pd.isna(row[106]) else ''
            s_apellido = fix_encoding(str(row[107])) if not pd.isna(row[107]) else ''
            p_nombre = fix_encoding(str(row[108])) if not pd.isna(row[108]) else ''
            o_nombre = fix_encoding(str(row[109])) if not pd.isna(row[109]) else ''
            
            # Additional cleanup
            def clean_str(s):
                if s.lower() == 'nan': return ''
                return s

            p_apellido = clean_str(p_apellido)
            s_apellido = clean_str(s_apellido)
            p_nombre = clean_str(p_nombre)
            o_nombre = clean_str(o_nombre)

            def clean_val(val):
                if pd.isna(val) or val == 'nan':
                    return 0
                try:
                    return float(val)
                except:
                    return 0

            obj, created = DatosCertificadoDIAN.objects.update_or_create(
                anio_gravable=2025,
                cedula=cedula,
                defaults={
                    'primer_apellido': p_apellido,
                    'segundo_apellido': s_apellido,
                    'primer_nombre': p_nombre,
                    'otros_nombres': o_nombre,
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
            )
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} rows...")
        except Exception as e:
            print(f"Error processing row {index} (Cedula: {cedula}): {e}")

    print(f"Finished! Total processed: {count}")

if __name__ == "__main__":
    import_dian_data()
