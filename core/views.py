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
                # Map some known apps to their dashboards, otherwise follow local logic
                if unica_app == 'CertificadosDIAN':
                    return redirect('certificados_dian:dashboard')
                elif unica_app == 'unificador_v1':
                    return redirect('/atencion/')
                # Removed redirect for horas_extras to use the new dashboard categories instead of the old hub view
            # Store for reuse in get_context_data to avoid re-querying
            request._allowed_apps = allowed_apps
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_superuser = user.is_superuser
        
        # 1. Get filtered lists from our context processor logic
        allowed_apps = getattr(self.request, '_allowed_apps', set())
        if not is_superuser and not allowed_apps:
             from usuarios.models import PermisoApp
             allowed_apps = set(
                 PermisoApp.objects.filter(user=user, permitido=True)
                 .values_list('app_label', flat=True)
             )

        def has_permission(slug):
            if is_superuser: return True
            if slug in ['A_00_Organigrama', 'usuarios', 'consultas_externas']: # Public apps
                return True
            if slug in allowed_apps: return True
            if 'horas_extras' in allowed_apps: return True
            if slug.startswith('CertificadosDIAN') and 'CertificadosDIAN' in allowed_apps: return True
            return False

        # Define Categories with their respective modules
        # This structure allows us to filter categories based on whether they have visible modules
        structure = [
            {
                'category': {'name': 'HOSPITALIZACION', 'slug': 'hospitalizacion', 'icon': 'M19 14l-7 7-7-7m14-8l-7 7-7-7', 'description': 'Gestión de pacientes en piso'},
                'modules': []
            },
            {
                'category': {'name': 'QUIRÚRGICAS', 'slug': 'quirofanos', 'icon': 'M22 12h-4l-3 9L9 3l-3 9H2', 'description': 'Cirugía, Anestesia y Procedimientos'},
                'modules': [
                    {'name': 'Consentimientos Informados', 'slug': 'ConsentimientosInformados', 'description': 'Autorizaciones y Firmas Electrónicas', 'url': '/consentimientos/', 'icon': 'M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z'},
                    {'name': 'Registro de Anestesia', 'slug': 'registro_anestesia', 'description': 'Registro Clínico de Anestesia (FRQUI-032)', 'url': '/registro-anestesia/create/', 'icon': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'},
                    {'name': 'Central de Mezclas', 'slug': 'CentralDeMezclas', 'description': 'Laboratorio de Preparaciones Estériles', 'url': '/central-mezclas/', 'icon': 'M11 10.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z M5.5 15.5l1.5-2 M17 15.5l-1.5-2 M2 22h20 M7 22l1-4.5 M17 22l-1-4.5'},
                    {'name': 'Trasplantes y Donación', 'slug': 'trasplantes_donacion', 'description': 'Gestión de Alertas y Trasplantes', 'url': '/modulo/trasplantes_donacion/', 'icon': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 8v4 M12 16h.01'},
                    {'name': 'Frecuencia Fetal', 'slug': 'frecuenciafetal', 'description': 'Monitoreo de Frecuencia Cardíaca Fetal', 'url': '/modulo/frecuenciafetal/', 'icon': 'M13 2L3 14h9l-1 8 10-12h-9l1-8z'},
                ]
            },
            {
                'category': {'name': 'SALA DE PARTOS', 'slug': 'gineco_obstetricia', 'icon': 'M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6', 'description': 'Maternidad y Neonatal'},
                'modules': [
                    {'name': 'SALA DE PARTOS', 'slug': 'unificador_v1', 'description': 'Consolidado de Atención de Partos', 'url': '/atencion/', 'icon': 'M19 14l-7 7-7-7m14-8l-7 7-7-7'},
                ]
            },
            {
                'category': {'name': 'TALENTO HUMANO', 'slug': 'talento_humano', 'icon': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z', 'description': 'Gestión de personal y nómina'},
                'modules': [
                    {'name': 'Organigrama Institucional', 'slug': 'A_00_Organigrama', 'description': 'Estructura Jerárquica - 6 Niveles', 'url': '/organigrama/', 'icon': 'M4 5h16v14H4z'},
                    {'name': 'Certificación por OPS', 'slug': 'certificados_laborales', 'description': 'Generación de documentos de contratación', 'url': '/certificados-laborales/', 'icon': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'},
                    {'name': 'Horas Extras', 'slug': 'hora_extra_list', 'description': 'Registro y control de tiempos suplementarios', 'url': '/horas-extras/asignacion-turnos/', 'icon': 'M12 8v4l3 3'},
                    {'name': 'Reportes de Nómina', 'slug': 'informes_dashboard', 'description': 'Consultas y reportes estadísticos', 'url': '/horas-extras/informes/', 'icon': 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'},
                    {'name': 'Conciliación Nómina vs Excel', 'slug': 'informe_consistencia_excel', 'description': 'Cruce con Excel Maestro de Cargos', 'url': '/horas-extras/informes/consistencia-excel/', 'icon': 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2'},
                    {'name': 'Resumen Planta Permanente', 'slug': 'reporte_personal_activo', 'description': 'Dashboard de personal activo de planta', 'url': '/horas-extras/informes/personal-activo/', 'icon': 'M17 20h5v-2a3 3 0 00-5.356-1.857'},
                    {'name': 'Resumen Planta Temporal', 'slug': 'reporte_personal_temporal', 'description': 'Reportes específicos de personal temporal', 'url': '/horas-extras/informes/personal-temporal/', 'icon': 'M17 20h5v-2a3 3 0 00-5.356-1.857'},
                    {'name': 'Listado Planta Permanente', 'slug': 'reporte_planta_listado', 'description': 'Listado detallado vinculado por planta', 'url': '/horas-extras/informes/planta-permanente/listado/', 'icon': 'M4 6h16M4 10h16M4 14h16M4 18h16'},
                    {'name': 'Listado Planta Temporal', 'slug': 'reporte_temporal_listado', 'description': 'Listado detallado vinculado por temporal', 'url': '/horas-extras/informes/planta-temporal/listado/', 'icon': 'M4 6h16M4 10h16M4 14h16M4 18h16'},
                    {'name': 'Personal por Áreas', 'slug': 'reporte_personal_area', 'description': 'Distribución por Centros de Costos', 'url': '/horas-extras/informes/personal-area/', 'icon': 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'},
                ]
            },
            {
                'category': {'name': 'ADMINISTRATIVO', 'slug': 'administrativo', 'icon': 'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5z', 'description': 'Gestión institucional'},
                'modules': [
                    {'name': 'Organigrama', 'slug': 'A_00_Organigrama', 'description': 'Estructura Jerárquica Institucional', 'url': '/organigrama/', 'icon': 'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5z'},
                    {'name': 'Presupuesto', 'slug': 'presupuesto', 'description': 'Gestión Presupuestal', 'url': '/presupuesto/', 'icon': 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2'},
                ]
            }
        ]

        # Process structure and filter based on permissions
        active_structure = []
        all_permitted_modules = []

        for item in structure:
            permitted_modules = [m for m in item['modules'] if has_permission(m['slug'])]
            
            # Ensure every module has a URL
            for m in permitted_modules:
                if 'url' not in m: m['url'] = f"/modulo/{m['slug']}/"
            
            if permitted_modules or has_permission(item['category']['slug']):
                active_structure.append({
                    'category': item['category'],
                    'modules': permitted_modules
                })
                all_permitted_modules.extend(permitted_modules)

        # Decide if we show the "Direct View" (skipped category level)
        # We skip the category step if the user has 1..6 modules total, 
        # making it "Dynamic" and "Less Clicky" as requested.
        show_direct_modules = (1 <= len(all_permitted_modules) <= 6) and not is_superuser

        context.update({
            'active_structure': active_structure,
            'dashboard_categories': [item['category'] for item in active_structure],
            'all_permitted_modules': all_permitted_modules,
            'show_direct_modules': show_direct_modules,
            'is_superuser': is_superuser
        })

        # Backward compatibility for existing templates (will eventually remove)
        context['quirofanos_modules'] = next((item['modules'] for item in structure if item['category']['slug'] == 'quirofanos'), [])
        context['gineco_modules'] = next((item['modules'] for item in structure if item['category']['slug'] == 'gineco_obstetricia'), [])
        context['administrativos'] = next((item['modules'] for item in structure if item['category']['slug'] == 'administrativo'), [])
        context['nav_talento_humano'] = next((item['modules'] for item in structure if item['category']['slug'] == 'talento_humano'), [])

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
