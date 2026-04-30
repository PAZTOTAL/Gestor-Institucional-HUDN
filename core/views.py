from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
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

def csrf_failure(request, reason=''):
    messages.warning(request, 'Tu sesión expiró. Por favor inicia sesión nuevamente.')
    return redirect('login')


class VariosPanelView(LoginRequiredMixin, TemplateView):
    template_name = 'core/varios_panel.html'

class HomeView(AccessControlMixin, TemplateView):
    permission_type = 'view'
    template_name = 'core/home.html'

    # Metadatos de categoría para la vista jerárquica (superusuarios).
    # Solo define nombre/icono/descripción del grupo — los módulos vienen de DB.
    CATEGORY_META = {
        'asistencial':    {'name': 'ASISTENCIAL',           'slug': 'asistencial',    'icon': 'M22 12h-4l-3 9L9 3l-3 9H2',                                    'description': 'Servicios Médicos y Asistenciales'},
        'administrativo': {'name': 'ADMINISTRATIVO',        'slug': 'administrativo', 'icon': 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5', 'description': 'Gestión Administrativa'},
        'juridica':       {'name': 'JURÍDICA',              'slug': 'juridica',       'icon': 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',                  'description': 'Asesoría y Defensa Legal'},
        'talento_humano': {'name': 'TALENTO HUMANO',        'slug': 'talento_humano', 'icon': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z', 'description': 'Gestión de personal y nómina'},
        'contabilidad':   {'name': 'CONTABILIDAD',          'slug': 'contabilidad',   'icon': 'M9 17v-2m3 2v-4m3 4v-6m2 10H5a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v14a2 2 0 01-2 2z', 'description': 'Certificados de Ingresos y Retenciones'},
        'financiera':     {'name': 'FINANCIERA',            'slug': 'financiera',     'icon': 'M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',   'description': 'Gestión contable y presupuestal'},
        'varios':         {'name': 'VARIOS',                'slug': 'varios',         'icon': 'M4 6h16M4 12h16M4 18h16',                                       'description': 'Formatos y herramientas generales'},
        'consultas':      {'name': 'CONSULTAS',             'slug': 'consultas',      'icon': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', 'description': 'Indicadores y Reportes'},
        'bienes_servicios': {'name': 'BIENES Y SERVICIOS',   'slug': 'bienes_servicios', 'icon': 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4', 'description': 'Almacén e Inventarios'},
    }

    # Categorías que pertenecen a cada subgerencia en la vista jerárquica
    SALUD_CATS     = {'asistencial', 'consultas'}
    FINANCIERA_CATS = {'talento_humano', 'financiera', 'contabilidad', 'juridica', 'administrativo', 'varios', 'bienes_servicios'}

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_superuser:
            from core.models import DashboardModule
            allowed_apps = getattr(request.user, '_permisos_apps_cache', set())

            # Redirección directa cuando el usuario tiene un único módulo permitido
            if len(allowed_apps) == 1:
                slug = next(iter(allowed_apps))
                mod = DashboardModule.objects.filter(slug=slug, is_active=True).values('url').first()
                if mod and mod['url']:
                    return redirect(mod['url'])

            request._allowed_apps = allowed_apps
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import DashboardModule

        user = self.request.user
        is_superuser = user.is_superuser
        allowed_apps = getattr(self.request, '_allowed_apps', set())

        # ── 1. Consultar módulos para TODOS (Prueba) ──────────────────────────
        modules_qs = DashboardModule.objects.filter(is_active=True)
        # if is_superuser:
        #     modules_qs = DashboardModule.objects.filter(is_active=True)
        # else:
        #     modules_qs = DashboardModule.objects.filter(is_active=True, slug__in=allowed_apps)

        all_modules = list(modules_qs.values('name', 'slug', 'description', 'url', 'icon', 'category'))

        # ── 2. Lista plana para la vista "Mis Aplicaciones" (TODOS) ───────────
        all_permitted_modules = []
        for m in all_modules:
            name = m['name']
            if name == 'UNIFICADOR-V1':
                name = 'SALA DE PARTOS'
            
            all_permitted_modules.append({
                'name': name, 
                'slug': m['slug'], 
                'description': m['description'],
                'url': m['url'] or f"/modulo/{m['slug']}/", 
                'icon': m['icon']
            })
        
        # Agregar reportes individuales solicitados como botones directos (Acceso Inmediato)
        all_permitted_modules.append({
            'name': 'Trazabilidad Pacientes',
            'slug': 'trazabilidad_pacientes',
            'description': 'Seguimiento Urgencias y Triage',
            'url': '/consultas/pacientes-urgencias/',
            'icon': 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'
        })
        all_permitted_modules.append({
            'name': 'Facturación y Ventas',
            'slug': 'facturacion_ventas',
            'description': 'Auditoría de Ventas y RIPS',
            'url': '/consultas/admin/?view=ventas&group_by=global',
            'icon': 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2'
        })
        all_permitted_modules.append({
            'name': 'Producción Médica',
            'slug': 'productividad_medica',
            'description': 'Indicadores de Productividad',
            'url': '/consultas/produccion-medico/',
            'icon': 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
        })
        
        all_permitted_modules.append({
            'name': 'Indicadores de Salud',
            'slug': 'indicadores_salud',
            'description': 'Dashboard de Gestión Hospitalaria',
            'url': '/consultas/salud/',
            'icon': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
        })
        
        all_permitted_modules.append({
            'name': 'Consultas e Indicadores',
            'slug': 'consultas_dashboard',
            'description': 'Dashboard General de Reportes',
            'url': '/?section=consultas',
            'icon': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
        })
        
        all_permitted_modules.append({
            'name': 'Inventarios Nexus',
            'slug': 'inventarios_nexus',
            'description': 'Consulta de Documentos e Inventario',
            'url': '/inventarios/documentos/',
            'icon': 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4'
        })
        
        show_direct_modules = True # Forzamos vista de botones directa

        # ── 3. Agrupar por categoría para la vista jerárquica ──────────────────
        cat_modules: dict = {}
        for m in all_modules:
            name = m['name']
            if name == 'UNIFICADOR-V1':
                name = 'SALA DE PARTOS'

            cat_modules.setdefault(m['category'], []).append({
                'name': name, 'slug': m['slug'], 'description': m['description'],
                'url': m['url'] or f"/modulo/{m['slug']}/", 'icon': m['icon']
            })

        active_structure = []
        for cat_slug, meta in self.CATEGORY_META.items():
            mods = cat_modules.get(cat_slug, [])
            if mods:
                active_structure.append({'category': meta, 'modules': mods})
                # Inyectar nav_slug para compatibilidad con base.html
                context[f"nav_{cat_slug}"] = mods

        # Mantener estas para compatibilidad específica del template home.html
        nav_asistenciales  = [i for i in active_structure if i['category']['slug'] in self.SALUD_CATS]
        nav_financiera_cat = [i for i in active_structure if i['category']['slug'] in self.FINANCIERA_CATS]

        # ── 4. Sección especial Consultas (Habilitado para todos en prueba) ───
        has_consultas = True 
        consultas_ctx = {
            'consultas': [
                {'name': 'Administrativas', 'slug': 'consultas_administrativas', 'description': 'Facturación y RIPS'},
                {'name': 'Asistenciales',   'slug': 'consultas_asistenciales',   'description': 'Indicadores Médicos'},
            ],
            'admin_reports': [
                {'name': 'Facturación Total', 'url': '/consultas/admin/?view=ventas&group_by=global'},
                {'name': 'Reportes RIPS',     'url': '/consultas/admin/?view=rips&group_by=global'},
            ],
            'salud_reports': [
                {'name': 'Indicadores de Salud',        'url': '/consultas/salud/'},
                {'name': 'Producción Médica',            'url': '/consultas/produccion-medico/'},
                {'name': 'Trazabilidad de Pacientes',    'url': '/consultas/pacientes-urgencias/'},
            ],
        }
        # Asegurar que nav_consultas sea detectado por el header
        context['nav_consultas'] = consultas_ctx['consultas']

        # ── 5. Construir contexto final ───────────────────────────────────────
        context.update({
            'is_superuser':          is_superuser,
            'all_permitted_modules': all_permitted_modules,
            'show_direct_modules':   show_direct_modules,
            'active_structure':      active_structure,
            'dashboard_categories':  [i['category'] for i in active_structure],
            'nav_asistenciales':     nav_asistenciales,
            'nav_financiera_cat':    nav_financiera_cat,
            **consultas_ctx,
        })
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
