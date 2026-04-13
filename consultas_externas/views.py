from django.shortcuts import render
from django.apps import apps
from django.http import HttpResponse, Http404
import csv
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from core.decorators import valida_acceso

@login_required
@valida_acceso('consultas_externas')
def index(request):
    """Lista todos los modelos de la app consultas_externas."""
    app_config = apps.get_app_config('consultas_externas')
    models = []
    for model in app_config.get_models():
        models.append({
            'name': model.__name__,
            'verbose_name': model._meta.verbose_name,
        })
    
    # Ordenar alfabéticamente por verbose_name
    models.sort(key=lambda x: x['verbose_name'])
    
    return render(request, 'consultas_externas/index.html', {'models': models})

@login_required
@valida_acceso('consultas_externas')
def export_users_csv(request, model_name):
    """Exporta los datos de un modelo a CSV (más rápido y compatible que Excel nativo sin libs extra)."""
    app_config = apps.get_app_config('consultas_externas')
    try:
        model = app_config.get_model(model_name)
    except LookupError:
        raise Http404("Modelo no encontrado")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{model_name}_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    
    # Encabezados
    fields = [field.name for field in model._meta.fields]
    writer.writerow(fields)

    # Datos
    # Usamos iterator() para mejorar uso de memoria en tablas grandes
    queryset = model.objects.using('readonly').all().iterator()
    
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in fields])

    return response

from django.db.models import Q
from django.core.paginator import Paginator

@login_required
@valida_acceso('consultas_externas')
def view_data(request, model_name):
    """Muestra y busca datos de un modelo específico."""
    app_config = apps.get_app_config('consultas_externas')
    try:
        model = app_config.get_model(model_name)
    except LookupError:
        raise Http404("Modelo no encontrado")

    query = request.GET.get('q', '')
    limit = request.GET.get('limit', '')
    order = request.GET.get('order', 'asc')

    object_list = model.objects.using('readonly').all()

    # Lógica de búsqueda genérica
    if query:
        search_query = Q()
        # Iterar sobre los campos para buscar en todos los de tipo texto/char
        for field in model._meta.fields:
            # Exclude TextField to avoid SQL Server 'ntext' incompatibilities with UPPER()
            if field.get_internal_type() in ['CharField']: 
                # OR condicional: busca si ALGUNO de los campos contiene el texto
                search_query |= Q(**{f'{field.name}__icontains': query})
        
        if search_query:
            object_list = object_list.filter(search_query)

    # 2. Orden
    pk_name = model._meta.pk.name if hasattr(model._meta, 'pk') and model._meta.pk else 'id'
    if order == 'desc':
        object_list = object_list.order_by(f'-{pk_name}')
    elif not object_list.ordered:
        object_list = object_list.order_by(pk_name)

    # 3. Límite
    items_per_page = 20
    if limit and limit.isdigit():
        object_list = object_list[:int(limit)]
        items_per_page = int(limit)

    paginator = Paginator(object_list, items_per_page) # Items dinámicos
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Obtener metadatos de campos para la cabecera de la tabla
    fields_metadata = []
    for field in model._meta.fields:
        fields_metadata.append({
            'name': field.name,
            'verbose_name': getattr(field, 'verbose_name', field.name) or field.name
        })

    return render(request, 'consultas_externas/data_view.html', {
        'model_name': model_name,
        'verbose_name': model._meta.verbose_name,
        'page_obj': page_obj,
        'fields': fields_metadata, 
        'query': query,
        'current_limit': limit,
        'current_order': order,
    })

from django.db import connections

@login_required
@valida_acceso('consultas_externas')
def table_stats(request):
    """Consulta directa a SQL Server para obtener listado de tablas y su cantidad de filas."""
    query = """
    SELECT 
        schema_name(t.schema_id) + '.' + t.name AS TableName,
        SUM(p.rows) AS RowCounts
    FROM 
        sys.tables t
    INNER JOIN      
        sys.indexes i ON t.OBJECT_ID = i.object_id
    INNER JOIN 
        sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
    WHERE 
        t.is_ms_shipped = 0
    GROUP BY 
        t.schema_id, t.name
    ORDER BY 
        RowCounts DESC
    """
    
    stats = []
    error_message = None
    
    try:
        with connections['readonly'].cursor() as cursor:
            cursor.execute(query)
            # fetchall retorna lista de tuplas (TableName, RowCounts)
            stats = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
    except Exception as e:
        error_message = f"Error consultando base de datos: {str(e)}"

    return render(request, 'consultas_externas/table_stats.html', {
        'stats': stats,
        'error_message': error_message
    })
