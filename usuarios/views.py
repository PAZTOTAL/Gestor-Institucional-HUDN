from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.db.models import Q
from core.mixins import AccessControlMixin
from django.apps import apps
from django.db import connections
from django.http import JsonResponse
from .forms import RegistroForm
from .models import PerfilUsuario, PermisoApp, PermisoModelo

class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'login'

class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = 'usuarios/registro.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create profile for new user
        PerfilUsuario.objects.get_or_create(user=self.object)
        
        # Otorga permiso automáticamente SOLO para la app CertificadosDIAN por defecto
        PermisoApp.objects.get_or_create(user=self.object, app_label="CertificadosDIAN", defaults={"permitido": True})
        
        return response

class PanelUsuariosView(AccessControlMixin, TemplateView):
    app_label = 'usuarios'
    template_name = 'usuarios/gestion_usuarios.html'
    model = User
    # We use CreateView just as a base, but we will mostly list and manage
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q')
        if query:
            usuarios = User.objects.filter(
                Q(username__icontains=query) | 
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query)
            ).order_by('-date_joined')
        else:
            usuarios = User.objects.all().order_by('-date_joined')
        
        context['usuarios'] = usuarios
        return context

class GestionPermisosView(AccessControlMixin, TemplateView):
    app_label = 'usuarios'
    template_name = 'usuarios/permisos_usuario.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('pk')
        target_user = User.objects.get(pk=user_id)
        perfil, _ = PerfilUsuario.objects.get_or_create(user=target_user)
        
        # Obtener todas las apps locales dinámicamente comprobando el directorio de instalación
        from django.apps import apps
        from django.conf import settings
        
        # Filtramos solo las apps cuyo path está dentro de BASE_DIR (las creadas por nosotros)
        local_apps = [
            app_config.label for app_config in apps.get_app_configs()
            if str(app_config.path).startswith(str(settings.BASE_DIR))
        ]
        
        # Get and merge with dynamic DashboardModules (External links or custom shortcuts)
        from core.models import DashboardModule
        db_modules = DashboardModule.objects.filter(is_active=True)
        
        # We'll use a set to avoid duplicates with django app labels
        all_app_slugs = set(local_apps)
        for db_mod in db_modules:
            all_app_slugs.add(db_mod.slug)
            
        app_permissions = []
        for app in sorted(list(all_app_slugs)):
            perm_app = PermisoApp.objects.filter(user=target_user, app_label=app).first()
            
            # Get models for this slug if it's a Django App
            app_models = []
            if app in local_apps:
                try:
                    app_config = apps.get_app_config(app)
                    for model in app_config.get_models():
                        model_name = model.__name__
                        perm_mod = PermisoModelo.objects.filter(user=target_user, app_label=app, model_name=model_name).first()
                        app_models.append({
                            'name': model_name,
                            'verbose_name': model._meta.verbose_name.title(),
                            'permitido': perm_mod.permitido if perm_mod else False
                        })
                except LookupError:
                    pass

            # Find display name (if in DB use name, else use slug)
            db_mod_info = db_modules.filter(slug=app).first()
            display_name = db_mod_info.name if db_mod_info else app.replace('_', ' ').title()

            app_permissions.append({
                'label': display_name,
                'slug': app,
                'permitido': perm_app.permitido if perm_app else False,
                'models': app_models,
                'is_db': db_mod_info is not None
            })
            
        context['target_user'] = target_user
        context['perfil'] = perfil
        context['app_permissions'] = app_permissions
        context['categorias'] = PerfilUsuario.CATEGORIAS
        return context

    def post(self, request, *args, **kwargs):
        user_id = self.kwargs.get('pk')
        target_user = User.objects.get(pk=user_id)
        perfil, _ = PerfilUsuario.objects.get_or_create(user=target_user)
        
        # Actualizar estado de usuario (Superuser y Staff)
        target_user.is_superuser = 'is_superuser' in request.POST
        target_user.is_staff = 'is_staff' in request.POST
        target_user.save()

        # Actualizar Categoría
        new_cat = request.POST.get('categoria')
        if new_cat:
            perfil.categoria = new_cat
            perfil.save()
            
        # PROCESAMIENTO DE PERMISOS
        # 1. Resetear todos los permisos actuales para este usuario
        PermisoApp.objects.filter(user=target_user).update(permitido=False)
        PermisoModelo.objects.filter(user=target_user).update(permitido=False)
        
        selected_apps = set(request.POST.getlist('apps'))
        selected_models = request.POST.getlist('models') # Formato: app_label.model_name
        
        # 2. Guardar permisos de modelos y recolectar apps implícitas
        apps_to_enable = selected_apps.copy()
        
        for full_name in selected_models:
            if '.' in full_name:
                app_label, model_name = full_name.split('.')
                apps_to_enable.add(app_label) # Asegurar que la app esté activa si un modelo lo está
                
                perm_m, created = PermisoModelo.objects.get_or_create(
                    user=target_user, 
                    app_label=app_label, 
                    model_name=model_name
                )
                perm_m.permitido = True
                perm_m.save()

        # 3. Guardar permisos de aplicaciones
        for app_slug in apps_to_enable:
            perm, created = PermisoApp.objects.get_or_create(user=target_user, app_label=app_slug)
            perm.permitido = True
            perm.save()
            
        return redirect('gestion_usuarios')

class ConfigPerfilView(LoginRequiredMixin, TemplateView):
    template_name = 'usuarios/config_perfil.html'

    def post(self, request, *args, **kwargs):
        perfil, _ = PerfilUsuario.objects.get_or_create(user=request.user)
        perfil.color_primario = request.POST.get('color_primario', perfil.color_primario)
        perfil.color_secundario = request.POST.get('color_secundario', perfil.color_secundario)
        perfil.color_fondo = request.POST.get('color_fondo', perfil.color_fondo)
        perfil.estilo_fondo = request.POST.get('estilo_fondo', perfil.estilo_fondo)
        perfil.save()
        return redirect('config_perfil')

def lookup_tercero_por_cedula(request):
    cedula = request.GET.get('cedula', '').strip()
    if not cedula:
        return JsonResponse({'found': False, 'message': 'Cédula no proporcionada'})
    
    try:
        Genpacien = apps.get_model('consultas_externas', 'Genpacien')
        Gentercer = apps.get_model('consultas_externas', 'Gentercer')
        
        data = {
            'found': False,
            'cedula': cedula,
            'primer_nombre': '',
            'segundo_nombre': '',
            'primer_apellido': '',
            'segundo_apellido': '',
            'direccion': '',
            'telefono': '',
            'fecha_nacimiento': '',
            'email_personal': '',
            'email_institucional': '',
            'nombre_completo': '',
            'sexo': '',
            'grupo_sanguineo': '',
            'rh': ''
        }
        
        # 1. Search in GENTERCER (Source for names)
        tercero = Gentercer.objects.using('readonly').filter(ternumdoc=cedula).first()
        if tercero:
            data['found'] = True
            data['primer_nombre'] = tercero.terprinom or ''
            data['segundo_nombre'] = tercero.tersegnom or ''
            data['primer_apellido'] = tercero.terpriape or ''
            data['segundo_apellido'] = tercero.tersegape or ''
            data['nombre_completo'] = f"{data['primer_nombre']} {data['segundo_nombre']} {data['primer_apellido']} {data['segundo_apellido']}"
            
        # 2. Search in GENPACIEN (Source for contact/personal details)
        paciente = Genpacien.objects.using('readonly').filter(pacnumdoc=cedula).first()
        if paciente:
            data['found'] = True
            # Prefer paciente names if available/longer? Usually they are the same.
            if not data['primer_nombre']:
                data['primer_nombre'] = paciente.pacprinom or ''
                data['segundo_nombre'] = paciente.pacsegnom or ''
                data['primer_apellido'] = paciente.pacpriape or ''
                data['segundo_apellido'] = paciente.pacsegape or ''
            
            if not data['nombre_completo'] and data['primer_nombre']:
                data['nombre_completo'] = f"{data['primer_nombre']} {data['segundo_nombre']} {data['primer_apellido']} {data['segundo_apellido']}"
            
            data['direccion'] = paciente.gpadirrhab or paciente.gpadirresex or ''
            data['telefono'] = paciente.gpatelresex or ''
            data['fecha_nacimiento'] = paciente.gpafecnac.strftime('%Y-%m-%d') if paciente.gpafecnac else ''
            data['email_personal'] = paciente.gpaemail or ''
            data['sexo'] = 'M' if paciente.gpasexpac == 1 else 'F' if paciente.gpasexpac == 2 else ''
        # 3. Buscar Usuario en GENUSUARIO (Dinámica Nexus)
        username_institucional = None
        es_cliente = True
        
        with connections['readonly'].cursor() as cursor:
            # Estrategia A: Búsqueda Directa por NumeroDocumento
            cursor.execute("SELECT USUNOMBRE, USUEMAIL FROM GENUSUARIO WHERE NumeroDocumento = %s AND USUESTADO = 1", [cedula])
            usu_row = cursor.fetchone()
            
            if usu_row:
                username_institucional = usu_row[0]
                data['email_institucional'] = usu_row[1] or ''
                es_cliente = False
            else:
                # Estrategia B: Búsqueda vía GENMEDICO / GENTERCER (Para personal médico/asistencial)
                sql_medico = """
                SELECT U.USUNOMBRE, U.USUEMAIL
                FROM GENUSUARIO U
                INNER JOIN GENMEDICO M ON U.USUNOMBRE = M.GMECODIGO
                INNER JOIN GENTERCER T ON M.GENTERCER = T.OID
                WHERE T.TERNUMDOC = %s AND U.USUESTADO = 1
                """
                cursor.execute(sql_medico, [cedula])
                usu_row = cursor.fetchone()
                if usu_row:
                    username_institucional = usu_row[0]
                    data['email_institucional'] = usu_row[1] or ''
                    es_cliente = False
                else:
                    # Estrategia C: Búsqueda por Nombre (Para personal administrativo sin cédula en GENUSUARIO)
                    if data['nombre_completo']:
                        # Normalizar nombre para la búsqueda (quitar espacios extra y pasar a mayúsculas)
                        nombre_limpio = " ".join(data['nombre_completo'].split()).upper()
                        sql_nombre = """
                        SELECT USUNOMBRE, USUEMAIL
                        FROM GENUSUARIO 
                        WHERE (UPPER(USUDESCRI) = %s OR UPPER(USUDESCRI) LIKE %s)
                        AND USUESTADO = 1
                        """
                        cursor.execute(sql_nombre, [nombre_limpio, f"%{nombre_limpio}%"])
                        usu_row = cursor.fetchone()
                        if usu_row:
                            username_institucional = usu_row[0]
                            data['email_institucional'] = usu_row[1] or ''
                            es_cliente = False

        data['username_institucional'] = username_institucional
        data['es_cliente'] = es_cliente

        if data['found']:
            return JsonResponse({'found': True, 'data': data})
        else:
            return JsonResponse({
                'found': False, 
                'message': 'No se encontró información para esta cédula en la base de datos institucional.'
            })
            
    except Exception as e:
        return JsonResponse({'found': False, 'message': f'Error en la búsqueda: {str(e)}'})
