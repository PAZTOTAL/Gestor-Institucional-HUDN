from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.apps import apps
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.text import slugify
from django.urls import reverse
from django.forms import modelform_factory
from django import forms
from django.db import models
from django.core.exceptions import PermissionDenied
from django.core.exceptions import PermissionDenied
from .mixins import AccessControlMixin
from .utils_excel import generate_excel_template, process_excel_import, get_model_safe
from usuarios.models import PermisoApp, PermisoModelo



class DynamicModelMixin:
    def get_model(self):
        module_name = self.kwargs.get('module_name')
        model_name = self.kwargs.get('model_name')
        return apps.get_model(module_name, model_name)

    def get_success_url(self):
        return reverse('table_detail', kwargs={
            'module_name': self.kwargs.get('module_name'),
            'model_name': self.kwargs.get('model_name')
        })

    def get_form_class(self):
        model = self.get_model()
        widgets = {}
        
        for field in model._meta.get_fields():
            if not field.concrete or field.auto_created:
                continue
                
            # Date Fields - Native Picker with Elegant Style
            if isinstance(field, models.DateField):
                widgets[field.name] = forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3.5 bg-white text-black font-bold border-2 border-blue-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm hover:border-blue-600'})
            elif isinstance(field, models.DateTimeField):
                widgets[field.name] = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full p-3.5 bg-white text-black font-bold border-2 border-blue-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm hover:border-blue-600'})
                
            # Integer Fields - Strict Integers
            elif isinstance(field, models.IntegerField):
                attrs = {
                    'max': '999999999999', 
                    'step': '1',
                    'onkeypress': 'return (event.charCode >= 48 && event.charCode <= 57)',
                    'class': 'w-full p-3.5 bg-white text-black font-bold border-2 border-blue-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm hover:border-blue-600'
                }
                
                # Auto-numeric Readonly Styling
                if 'CONSEC' in field.name.upper():
                    attrs['readonly'] = 'readonly'
                    attrs['class'] = 'w-full p-3.5 bg-gray-200 text-gray-700 font-bold border-2 border-gray-400 rounded-xl cursor-not-allowed shadow-inner'
                
                widgets[field.name] = forms.NumberInput(attrs=attrs)
            
            # Decimal/Float Fields - Allow decimals
            elif isinstance(field, (models.DecimalField, models.FloatField)):
                widgets[field.name] = forms.NumberInput(attrs={
                    'max': '999999999999',
                    'step': 'any',
                    'onkeypress': 'return (event.charCode >= 48 && event.charCode <= 57) || event.charCode == 46',
                    'class': 'w-full p-3.5 bg-white text-black font-bold border-2 border-blue-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm hover:border-blue-600'
                })
                
            # Text Fields
            elif isinstance(field, models.CharField):
                widgets[field.name] = forms.TextInput(attrs={'class': 'w-full p-3.5 bg-white text-black font-bold border-2 border-blue-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm hover:border-blue-600'})
            elif isinstance(field, models.TextField):
                widgets[field.name] = forms.Textarea(attrs={'rows': 3, 'class': 'w-full p-3.5 bg-white text-black font-bold border-2 border-blue-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm hover:border-blue-600'})
                
            # Boolean Fields (Checkbox)
            elif isinstance(field, models.BooleanField):
                 widgets[field.name] = forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-primary rounded focus:ring-primary border-gray-300'})

            # ForeignKeys - Add "Quick Create" link data
            elif isinstance(field, models.ForeignKey):
                try:
                    related_model = field.related_model
                    # Handle string references if lazy
                    if isinstance(related_model, str):
                        related_model = apps.get_model(related_model)
                        
                    rel_app = related_model._meta.app_label
                    rel_model = related_model._meta.model_name
                    
                    # We can't easily reverse here without request context issues sometimes, 
                    # but usually ok. Safer to build string or use reverse lazy? 
                    # Let's use reverse directly as this method runs in view context usually
                    try:
                        add_url = reverse('table_create', kwargs={'module_name': rel_app, 'model_name': rel_model})
                    except:
                        add_url = ""
                        
                    attrs = {
                        'class': 'w-full p-3.5 bg-white text-black font-bold border-2 border-blue-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm hover:border-blue-600',
                        'data_add_url': add_url,
                        'data_related_name': related_model._meta.verbose_name
                    }
                    widgets[field.name] = forms.Select(attrs=attrs)
                except Exception as e:
                     # Fallback if anything fails (e.g. strict checking)
                     widgets[field.name] = forms.Select(attrs={'class': 'w-full p-3.5 bg-white text-black font-bold border-2 border-blue-400 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm hover:border-blue-600'})


        # Define separate list for exclusion
        exclude_fields = ['PK', 'OID', 'usuario']
        for field in model._meta.get_fields():
            if field.name.startswith(('DICCIONARIO', 'INVALID', 'SHORT_GARBAGE')):
                exclude_fields.append(field.name)

        return modelform_factory(model, exclude=exclude_fields, widgets=widgets)

class DynamicCreateView(AccessControlMixin, DynamicModelMixin, CreateView):
    permission_type = 'add'
    template_name = 'core/form_generic.html'

    def get_initial(self):
        initial = super().get_initial()
        model = self.get_model()
        
        # Auto-increment fields containing 'CONSEC'
        for field in model._meta.get_fields():
            if field.concrete and 'CONSEC' in field.name.upper():
                max_val = model.objects.aggregate(models.Max(field.name))[f'{field.name}__max']
                initial[field.name] = (max_val or 0) + 1
                
        return initial

    def form_valid(self, form):
        if hasattr(form.instance, 'usuario'):
            form.instance.usuario = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_slug'] = self.kwargs.get('module_name')
        context['model_slug'] = self.kwargs.get('model_name')
        context['model_name'] = self.get_model()._meta.verbose_name
        context['model_name'] = self.get_model()._meta.verbose_name
        
        # Custom Label for Juridica
        if context['module_slug'] == 'juridica':
            context['action'] = 'Cargar'
        else:
            context['action'] = 'Crear'
        return context

class DynamicUpdateView(AccessControlMixin, DynamicModelMixin, UpdateView):
    permission_type = 'change'
    template_name = 'core/form_generic.html'

    def form_valid(self, form):
        if hasattr(form.instance, 'usuario'):
            form.instance.usuario = self.request.user
        return super().form_valid(form)


    def get_queryset(self):
        return self.get_model().objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_slug'] = self.kwargs.get('module_name')
        context['model_slug'] = self.kwargs.get('model_name')
        context['model_name'] = self.get_model()._meta.verbose_name
        context['action'] = 'Editar'
        return context

class DynamicDeleteView(AccessControlMixin, DynamicModelMixin, DeleteView):
    permission_type = 'delete'
    template_name = 'core/confirm_delete.html'

    def get_queryset(self):
        return self.get_model().objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module_slug'] = self.kwargs.get('module_name')
        context['model_slug'] = self.kwargs.get('model_name')
        context['model_name'] = self.get_model()._meta.verbose_name
        return context

def render_to_pdf(template_src, context_dict={}):
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from django.http import HttpResponse
    import io
    
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

class VariosPanelView(LoginRequiredMixin, TemplateView):
    template_name = 'core/varios_panel.html'

class HomeView(AccessControlMixin, TemplateView):
    permission_type = 'view'
    template_name = 'core/home.html'

    def dispatch(self, request, *args, **kwargs):
        # Bloquear navegación a Home si solo tienen 1 permiso (su app dedicada)
        if request.user.is_authenticated and not request.user.is_superuser:
            # Single query to get all allowed apps for redirect check
            allowed_apps = set(
                PermisoApp.objects.filter(user=request.user, permitido=True)
                .values_list('app_label', flat=True)
            )
            if len(allowed_apps) == 1:
                unica_app = next(iter(allowed_apps))
                if unica_app == 'CertificadosDIAN':
                    return redirect('certificados_dian:dashboard')
            # Store for reuse in get_context_data to avoid re-querying
            request._allowed_apps = allowed_apps
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
                    
        # Categorize modules into Healthcare and Administrative groups
        asistenciales = [
            {'name': 'Registro de Anestesia', 'slug': 'registro_anestesia', 'description': 'Registro Clínico de Anestesia (FRQUI-032)', 'url': '/registro-anestesia/create/', 'icon': 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2 14 8 20 8 M16 13H8 M16 17H8 M10 9H9H8'},
            {'name': 'UNIFICADOR-V1', 'slug': 'unificador_v1', 'description': 'Historia Clínico y Partograma', 'url': '/atencion/', 'icon': 'M9 12h.01 M15 12h.01 M10 16a2.5 2.5 0 0 0 4 0 M12 22a7 7 0 1 0 0-14 7 7 0 0 0 0 14z M12 8V2 M5.88 10.9a3.5 3.5 0 1 1 5.24 4.77 M18.12 10.9a3.5 3.5 0 1 0-5.24 4.77'},
            {'name': 'Consentimientos Informados', 'slug': 'ConsentimientosInformados', 'description': 'Autorizaciones y Firmas Electrónicas', 'url': '/consentimientos/', 'icon': 'M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z'},
            {'name': 'Central de Mezclas', 'slug': 'CentralDeMezclas', 'description': 'Laboratorio de Preparaciones Estériles', 'url': '/central-mezclas/', 'icon': 'M16.3 3.4 12 10V2M11 10.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z M5.5 15.5l1.5-2 M17 15.5l-1.5-2 M2 22h20 M7 22l1-4.5 M17 22l-1-4.5'},
        ]
        
        administrativos = [
            {'name': 'Organigrama', 'slug': 'A_00_Organigrama', 'description': 'Estructura Jerárquica Institucional (6 Niveles)', 'url': '/organigrama/', 'icon': 'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z'},
            {'name': 'Generales y Seguridad', 'slug': 'usuarios', 'description': 'Configuración general y seguridad'},
            {'name': 'Consultas Base Externa', 'slug': 'consultas_externas', 'description': 'Consulta de datos GENTERCER y otros', 'url': '/consultas-externas/'},
            {'name': 'Talento Humano', 'slug': 'horas_extras', 'description': 'Gestión de Personal: Horas Extras e Informes', 'url': '/horas-extras/', 'icon': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z'},
            {'name': 'Formatos Institucionales', 'slug': 'BasesGenerales', 'description': 'Gestión de formatos y códigos FRXXX', 'url': '/modulo/BasesGenerales/tabla/Formatos_Hudn/', 'icon': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'},
            {'name': 'Presupuesto', 'slug': 'presupuesto', 'description': 'Gestión Presupuestal (CDP, RP, Obligaciones)', 'url': '/presupuesto/'},
            {'name': 'Bases Generales', 'slug': 'BasesGenerales', 'description': 'Configuración de bases generales'},
            {'name': 'Estudio De Conveniencia', 'slug': 'EstudioDeConveniencia', 'description': 'Generación de Estudios Previos', 'icon': 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2 14 8 20 8 M16 13H8 M16 17H8 M10 9H9H8'},
        ]

        consultas = [
            {'name': 'Administrativas', 'slug': 'consultas_administrativas', 'description': 'Facturación, RIPS y Aseguradoras', 'icon': 'bi-cash-stack'},
            {'name': 'Asistenciales', 'slug': 'consultas_asistenciales', 'description': 'Indicadores Médicos y Salud', 'icon': 'bi-activity'},
        ]
        
        # We also need the specific report links for the sub-sections
        admin_reports = [
            {'name': 'Facturación Total', 'url': '/consultas/admin/?view=ventas&group_by=global', 'description': 'Resumen global de ventas'},
            {'name': 'Facturación por Aseguradora', 'url': '/consultas/admin/?view=ventas&group_by=aseguradora', 'description': 'Ventas agrupadas por pagador'},
            {'name': 'Facturación por Paciente', 'url': '/consultas/admin/?view=ventas&group_by=paciente', 'description': 'Detalle de cargos por usuario'},
            {'name': 'Reportes RIPS', 'url': '/consultas/admin/?view=rips&group_by=global', 'description': 'Registros RIPS Procesados'},
        ]
        
        salud_reports = [
            {'name': 'Indicadores de Salud', 'url': '/consultas/salud/', 'description': 'Estadísticas Médicas'},
            {'name': 'Producción Médica', 'url': '/consultas/produccion-medico/', 'description': 'Informe de atenciones por profesional'},
            {'name': 'Trazabilidad de Pacientes', 'url': '/consultas/pacientes-urgencias/', 'description': 'Seguimiento de pacientes activos en todo el hospital'},
        ]
        
        # Filter based on permissions - OPTIMIZED: single query instead of N+1
        if not self.request.user.is_superuser:
            # Reuse the set from dispatch if available, otherwise fetch once
            allowed_apps = getattr(self.request, '_allowed_apps', None)
            if allowed_apps is None:
                allowed_apps = set(
                    PermisoApp.objects.filter(
                        user=self.request.user, permitido=True
                    ).values_list('app_label', flat=True)
                )

            # Filter in Python using the pre-fetched set (0 extra queries)
            asistenciales = [m for m in asistenciales if m['slug'] in allowed_apps]
            administrativos = [m for m in administrativos if m['slug'] in allowed_apps]
            
            # Filter Consultas
            if 'consultas' not in allowed_apps:
                consultas = []
                admin_reports = []
                salud_reports = []
        
        # Add URL to each module
        for mod in asistenciales + administrativos:
            if 'url' not in mod:
                mod['url'] = f"/modulo/{mod['slug']}/"
            
        context['asistenciales'] = asistenciales
        context['administrativos'] = administrativos
        context['consultas'] = consultas
        context['admin_reports'] = admin_reports
        context['salud_reports'] = salud_reports
        return context

class ModuleDetailView(AccessControlMixin, TemplateView):
    permission_type = 'view'
    template_name = 'core/module_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('module_name')
        
        # Find module name for display
        module_display_name = slug.replace('_', ' ').title()
        
        # Get all models
        project_models = apps.get_app_config(slug).get_models()
        
        module_models = []
        for model in project_models:
            model_name = model.__name__
            
            # Check for explicit permission
            if not self.request.user.is_superuser:
                perm = PermisoModelo.objects.filter(
                    user=self.request.user, 
                    app_label=slug, 
                    model_name=model_name
                ).first()
                # Hide if permission exists and is False
                if perm and not perm.permitido:
                    continue
            
            module_models.append({
                'name': model_name,
                'verbose_name': model._meta.verbose_name,
                'description': model.__doc__ or "",
                'slug': model_name
            })
        
        context['module_name'] = module_display_name
        context['module_slug'] = slug
        context['models'] = module_models
        return context

class TableDetailView(AccessControlMixin, TemplateView):
    permission_type = 'view'
    template_name = 'core/table_detail.html'
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_slug = self.kwargs.get('module_name')
        model_name = self.kwargs.get('model_name')
        context['module_slug'] = module_slug
        context['model_slug'] = model_name

        # Get the model class using app registry inside a loop or lookup
        try:
            model = apps.get_model(module_slug, model_name)
        except LookupError:
            model = None

        if model:
            # Full object queryset for pagination
            q = self.request.GET.get('q', '')
            limit = self.request.GET.get('limit', '')
            order = self.request.GET.get('order', 'asc')
            
            queryset = model.objects.all()
            
            # 1. Búsqueda
            if q:
                from django.db.models import Q
                search_query = Q()
                for field in model._meta.fields:
                    if field.get_internal_type() in ['CharField', 'TextField', 'IntegerField', 'AutoField']:
                         search_query |= Q(**{f'{field.name}__icontains': q})
                queryset = queryset.filter(search_query)
            
            # 2. Orden
            if order == 'desc':
                queryset = queryset.order_by('-pk' if hasattr(model._meta, 'pk') else '-id')
            else:
                queryset = queryset.order_by('pk' if hasattr(model._meta, 'pk') else 'id')
                
            # 3. Límite (si hay limit, desactivamos paginación efectiva mostrando todo el bloque)
            effective_paginate_by = self.paginate_by
            if limit and limit.isdigit():
                queryset = queryset[:int(limit)]
                effective_paginate_by = int(limit)

            # Simple pagination
            paginator = Paginator(queryset, effective_paginate_by)
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            # Get field names for header
            fields = [f.name for f in model._meta.get_fields() if f.concrete and not f.is_relation and f.name != 'id'] # Show concrete non-rel fields
            # Better approach: Show all concrete fields including FKs (as strings)
            fields = [f.name for f in model._meta.get_fields() if f.concrete]
            
            # Prepare rows for template (needs pk + values list)
            rows = []
            for obj in page_obj:
                row_values = []
                for field in fields:
                    val = getattr(obj, field)
                    if hasattr(val, 'all'): # m2m
                        val = ", ".join([str(i) for i in val.all()])
                    row_values.append(val)
                
                rows.append({
                    'pk': obj.pk,
                    'values': row_values
                })
            
            context['model_name'] = model._meta.verbose_name
            
            # Custom Label for Juridica
            if module_slug == 'juridica':
                context['create_label'] = 'Cargar Nuevo'
            else:
                context['create_label'] = 'Crear Nuevo'
            context['page_obj'] = page_obj
            context['rows'] = rows
            context['fields'] = fields
            context['is_paginated'] = page_obj.has_other_pages()
            
            # Pasar parámetros actuales para mantener filtros en paginación/UI
            context['query'] = q
            context['current_limit'] = limit
            context['current_order'] = order
        
        return context

class DynamicExcelTemplateView(AccessControlMixin, TemplateView):
    permission_type = 'view'
    
    def get(self, request, *args, **kwargs):
        module_name = kwargs.get('module_name')
        model_name = kwargs.get('model_name')
        
        model = get_model_safe(module_name, model_name)
        if not model:
            from django.http import Http404
            raise Http404("Modelo no encontrado")
            
        bio = generate_excel_template(model)
        
        from django.http import HttpResponse
        response = HttpResponse(
            bio.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = f"{model_name}_plantilla.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

class DynamicImportExcelView(AccessControlMixin, TemplateView):
    permission_type = 'add'
    template_name = 'core/table_detail.html'

    def post(self, request, *args, **kwargs):
        module_name = kwargs.get('module_name')
        model_name = kwargs.get('model_name')
        
        model = get_model_safe(module_name, model_name)
        if not model:
            from django.http import Http404
            raise Http404("Modelo no encontrado")
            
        file = request.FILES.get('file')
        if not file:
            from django.contrib import messages
            messages.error(request, "Debe adjuntar un archivo.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        preview = request.POST.get('preview') == '1'
        
        result = process_excel_import(request, model, file, preview=preview)
        
        from django.contrib import messages
        if result.get('response'):
            if preview:
                messages.warning(request, f"VISTA PREVIA: {result['message']} Descargando reporte de errores.")
            else:
                messages.error(request, f"Importación fallida: {result['message']}")
            return result['response']
        
        if result['success']:
            if preview:
                messages.info(request, f"VISTA PREVIA: Se importarían {result['count']} registros correctamente.")
            else:
                messages.success(request, f"Éxito: {result['message']}")
        else:
            messages.error(request, result['message'])
            
        return redirect(request.META.get('HTTP_REFERER', '/'))
