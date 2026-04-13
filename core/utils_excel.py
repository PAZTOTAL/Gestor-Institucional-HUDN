import io
import csv
from openpyxl import Workbook, load_workbook
from io import BytesIO
from django.http import HttpResponse
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect
from django.apps import apps
from django.db import models

def get_model_safe(module_name, model_name):
    """
    Safely retrieves a model class given an app label (module_name) and model name.
    """
    try:
        return apps.get_model(module_name, model_name)
    except LookupError:
        return None

def generate_excel_template(model):
    """
    Generates an Excel template (BytesIO) for a given model.
    Includes headers for all editable fields.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = model._meta.verbose_name[:31]  # Excel limits sheet names to 31 chars

    # Determine fields to include
    headers = []
    
    # Logic to prioritize fields: 
    # 1. ForeignKeys (first, matching import logic)
    # 2. 'codigo' if exists
    # 3. 'nombre' if exists
    # 4. Other fields
    
    fk_fields = [f.name for f in model._meta.fields if f.is_relation and f.many_to_one and f.name not in ('usuario',)]
    other_fields = [f.name for f in model._meta.fields if not f.is_relation and f.name != 'id'] # ID is auto usually
    
    # Sorting for usability
    final_headers = []
    
    # Add ForeignKeys first (often dependencies)
    final_headers.extend(fk_fields)
    
    # Add rest
    final_headers.extend(other_fields)
    
    ws.append(final_headers)
    
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio

def process_excel_import(request, model, file, preview=False):
    """
    Processes an uploaded Excel file to import data into the model.
    Returns a result dict: {'success': Bool, 'message': Str, 'errors': List, 'count': Int, 'response': HttpResponse|None}
    """
    print(f"--- INICIANDO IMPORTACIÓN PARA {model._meta.model_name} ---")
    try:
        wb = load_workbook(file, data_only=True)
        ws = wb.active
    except Exception as e:
        print(f"ERROR LECTURA: {e}")
        return {'success': False, 'message': f"Error al leer archivo: {e}", 'errors': []}

    headers = [cell.value for cell in ws[1]]
    print(f"ENCABEZADOS ENCONTRADOS: {headers}")
    
    if not headers:
        return {'success': False, 'message': "El archivo no tiene encabezados.", 'errors': []}

    # Map headers to fields (Case Insensitive)
    valid_map = {} # col_idx -> field_name
    normalized_fields = {f.name.lower(): f.name for f in model._meta.get_fields()}
    
    for idx, h in enumerate(headers):
        if not h: continue
        h_str = str(h).strip()
        h_lower = h_str.lower()
        
        if h_lower in normalized_fields:
             valid_map[idx] = normalized_fields[h_lower]
            
    print(f"MAPA VALIDO: {valid_map}")
    
    if not valid_map:
        return {'success': False, 'message': "Ningún encabezado coincide (Verifique mayúsculas/minúsculas).", 'errors': []}

    errors = []
    created_count = 0
    
    try:
        with transaction.atomic():
            sid = transaction.savepoint()
            
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row): continue
                
                row_data = {}
                row_errors = []
                
                for col_idx, field_name in valid_map.items():
                    val = row[col_idx]
                    field = model_fields[field_name]
                    
                    if isinstance(val, str):
                        val = val.strip()
                    if val == "":
                        val = None
                        
                    # FK Resolving logic
                    if val is not None and field.is_relation and field.many_to_one:
                        related = field.related_model
                        fk_obj = None
                        
                        # Try 'codigo'
                        if hasattr(related, 'codigo'):
                            try:
                                fk_obj = related.objects.get(codigo=val)
                            except related.DoesNotExist:
                                pass
                        
                        # Try PK
                        if not fk_obj:
                            try:
                                fk_obj = related.objects.get(pk=val)
                            except (related.DoesNotExist, ValueError):
                                pass
                                
                        if fk_obj:
                            val = fk_obj
                        else:
                            row_errors.append(f"No se halló '{field_name}' con valor '{val}'")
                            continue
                    
                    row_data[field_name] = val
                
                # Auto-fill defaults logic
                if 'descripcion' in row_data and row_data.get('descripcion') and not row_data.get('nombre'):
                    row_data['nombre'] = row_data['descripcion'][:200] # Truncate to max_length
                
                if row_errors:
                    errors.append({'fila': row_idx, 'error': "; ".join(row_errors)})
                    continue

                try:
                    instance = model(**row_data)
                    if hasattr(instance, 'usuario') and request.user.is_authenticated:
                        instance.usuario = request.user
                    instance.full_clean()
                    instance.save()
                    created_count += 1
                except Exception as e:
                    errors.append({'fila': row_idx, 'error': str(e)})

            if errors or preview:
                transaction.savepoint_rollback(sid)
            else:
                transaction.savepoint_commit(sid)

    except Exception as e:
        return {'success': False, 'message': f"Error crítico: {e}", 'errors': []}

    # Generate Error CSV if needed
    if errors:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="errores_{model._meta.model_name}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Fila', 'Error'])
        for err in errors:
            writer.writerow([err['fila'], err['error']])
        
        return {
            'success': False, 
            'message': f"Se encontraron {len(errors)} errores.", 
            'errors': errors, 
            'response': response,
            'preview_count': created_count if preview else 0
        }

    return {
        'success': True, 
        'message': f"Se procesaron {created_count} registros.", 
        'count': created_count
    }
