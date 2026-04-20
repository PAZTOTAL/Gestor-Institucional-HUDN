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
        if request.user.is_authenticated and not request.user.is_superuser:
            allowed_apps = set(
                PermisoApp.objects.filter(user=request.user, permitido=True)
                .values_list('app_label', flat=True)
            )
            
            # 1. Definir Mapeo de Equivalencias (App Label <-> Slug)
            # Esto asegura que dar permiso a la App o al Módulo funcione igual
            equiv_map = {
                'certificados_laborales': 'mvp',
                'mvp': 'certificados_laborales',
            }
            
            # Expandir allowed_apps con equivalencias
            final_perms = allowed_apps.copy()
            for app in allowed_apps:
                if app in equiv_map:
                    final_perms.add(equiv_map[app])
            
            # 2. Redirección Directa para Usuarios con 1 solo módulo (Skip Dashboard)
            if len(allowed_apps) == 1:
                unica_app = next(iter(allowed_apps))
                redirect_map = {
                    'CertificadosDIAN': 'certificados_dian:dashboard',
                    'unificador_v1': '/atencion/',
                    'certificados_laborales': '/certificados-laborales/',
                    'mvp': '/certificados-laborales/',
                    'horas_extras': '/horas-extras/asignacion-turnos/',
                    'registro_anestesia': '/registro-anestesia/create/',
                    'defenjur': '/defenjur/',
                    'presupuesto': '/presupuesto/',
                    'A_00_Organigrama': '/organigrama/'
                }
                
                target = redirect_map.get(unica_app)
                if target:
                    return redirect(target)
            
            request._allowed_apps = final_perms
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_superuser = user.is_superuser
        allowed_apps = getattr(self.request, '_allowed_apps', set())
        
        # Función de validación robusta y ESTRICTA
        def has_permission(slug):
            if is_superuser: return True
            
            # 1. Validación de coincidencia exacta (incluye mapeo de equivalencias previo)
            if slug in allowed_apps: return True
            
            # 2. Casos especiales de mapeo manual (Solo si el slug en DB es distinto al permiso)
            # Actualmente cubierto por final_perms en dispatch, pero se puede reforzar aquí si es necesario.
                
            return False

        # 1. Definir lista base de módulos (hardcoded para iconos/descripciones detalladas)
        # pero ahora solo como un complemento. El motor principal será la base de datos.
        hardcoded_metadata = {
            'A_00_Organigrama': {'name': 'Organigrama Institucional', 'icon': 'M4 5h16v14H4z'},
            'mvp': {'name': 'Certificación por OPS', 'url': '/certificados-laborales/'},
            'hora_extra_list': {'name': 'Horas Extras', 'url': '/horas-extras/asignacion-turnos/'},
            # ... se pueden añadir más aquí si se desea sobreescribir la DB
        }

        # 2. Obtener TODOS los módulos de la base de datos que el usuario tiene permitido
        from core.models import DashboardModule
        from django.db.models import Q
        
        db_modules = DashboardModule.objects.filter(is_active=True)
        permitted_db_modules = []
        for m in db_modules:
            if has_permission(m.slug):
                meta = hardcoded_metadata.get(m.slug, {})
                permitted_db_modules.append({
                    'name': meta.get('name', m.name),
                    'slug': m.slug,
                    'description': m.description,
                    'url': meta.get('url', m.url or f"/modulo/{m.slug}/"),
                    'icon': meta.get('icon', m.icon),
                    'category': m.category
                })

        # 3. Agrupar por categorías para la estructura del Dashboard
        categories_map = {
            'asistencial': {'name': 'HOSPITALIZACION / SALUD', 'slug': 'asistencial', 'icon': 'M22 12h-4l-3 9L9 3l-3 9H2'},
            'talento_humano': {'name': 'TALENTO HUMANO', 'slug': 'talento_humano', 'icon': 'M17 20h5...'},
            'financiera': {'name': 'FINANZAS', 'slug': 'financiera', 'icon': 'M12 1v22...'},
            'juridica': {'name': 'JURÍDICA', 'slug': 'juridica', 'icon': 'M12 22s8-4...'},
            'contabilidad': {'name': 'CONTABILIDAD', 'slug': 'contabilidad', 'icon': 'M9 5H7...'},
            'consultas': {'name': 'CONSULTAS', 'slug': 'consultas', 'icon': 'M9 17v-2...'},
            'varios': {'name': 'VARIOS', 'slug': 'varios', 'icon': 'M12 2L2 7...'}
        }

        active_structure = []
        all_permitted_modules = permitted_db_modules

        # Agrupar módulos en la estructura activa
        from itertools import groupby
        from operator import itemgetter
        
        # Ordenar por categoría para el groupby
        all_permitted_modules.sort(key=itemgetter('category'))
        
        for cat_slug, modules_gen in groupby(all_permitted_modules, key=itemgetter('category')):
            modules_list = list(modules_gen)
            cat_info = categories_map.get(cat_slug, {'name': cat_slug.upper(), 'slug': cat_slug, 'icon': ''})
            
            active_structure.append({
                'category': cat_info,
                'modules': modules_list
            })
            # Poblar variables específicas para el template (nav_...)
            context[f'nav_{cat_slug}'] = modules_list

        # Filtros específicos para sub-secciones de Salud (Compatibilidad con template)
        context['quirofanos_modules'] = [m for m in all_permitted_modules if m['category'] == 'asistencial']
        context['gineco_modules'] = [m for m in all_permitted_modules if m['category'] == 'asistencial']
        # Nota: Se pueden granular más si hay categorías específicas en DB para esto.

        # Decide if we show the "Direct View" (skipped category level)
        show_direct_modules = (1 <= len(all_permitted_modules) <= 6) and not is_superuser

        context.update({
            'active_structure': active_structure,
            'dashboard_categories': [item['category'] for item in active_structure],
            'all_permitted_modules': all_permitted_modules,
            'show_direct_modules': show_direct_modules,
            'is_superuser': is_superuser
        })

        # Consultas section
        if has_permission('consultas'):
             context.update({
                'consultas': [
                    {'name': 'Administrativas', 'slug': 'consultas_administrativas', 'description': 'Facturación y RIPS', 'icon': 'bi-cash-stack'},
                    {'name': 'Asistenciales', 'slug': 'consultas_asistenciales', 'description': 'Indicadores Médicos', 'icon': 'bi-activity'},
                ],
                'admin_reports': [
                    {'name': 'Facturación Total', 'url': '/consultas/admin/?view=ventas&group_by=global'},
                    {'name': 'Reportes RIPS', 'url': '/consultas/admin/?view=rips&group_by=global'},
                ],
                'salud_reports': [
                    {'name': 'Indicadores de Salud', 'url': '/consultas/salud/'},
                    {'name': 'Producción Médica', 'url': '/consultas/produccion-medico/'},
                ]
             })
        else:
            context.update({'consultas': [], 'admin_reports': [], 'salud_reports': []})

        return context
        return context

class ModuleDetailView(AccessControlMixin, TemplateView):
    permission_type = 'view'
    template_name = 'core/module_detail.html'

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.get('module_name')
        try:
            apps.get_app_config(slug)
        except LookupError:
            from django.contrib import messages
            messages.error(request, f'El módulo "{slug}" no está instalado.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

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
