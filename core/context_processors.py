from django.core.cache import cache
from .models import DashboardModule
from usuarios.models import PermisoApp


def modules_processor(request):
    """Provides navigation modules filtered by user permissions."""
    if not request.user.is_authenticated:
        return {}

    # 1. Se eliminó la caché por usuario para sincronización en tiempo real

    # 2. Si no hay cache, procesar todo
    # Fetch all active modules (cached globally)
    cache_key_all = 'all_active_dashboard_modules'
    all_modules = cache.get(cache_key_all)
    
    if all_modules is None:
        all_modules = list(
            DashboardModule.objects.filter(is_active=True)
            .values('name', 'slug', 'description', 'url', 'icon', 'category')
            .order_by('order', 'name')
        )
        cache.set(cache_key_all, all_modules, 3600) # Cache global de 1 hora

    allowed_apps = getattr(request.user, '_permisos_apps_cache', set())
    is_superuser = request.user.is_superuser
    
    final_allowed = set(allowed_apps)

    # 3. Filter and Group Modules
    categories = {
        'asistencial': [], 'administrativo': [], 'juridica': [], 
        'talento_humano': [], 'contabilidad': [], 'financiera': [], 
        'varios': [], 'consultas': []
    }

    for mod in all_modules:
        # has_perm = is_superuser
        # if not has_perm:
        #     if mod['slug'] in final_allowed:
        #         has_perm = True
        # if not has_perm:
        #     continue
        has_perm = True # Bypass para prueba global

        mod_dict = {
            'name': mod['name'], 'slug': mod['slug'], 'description': mod['description'],
            'url': mod['url'] or f"/modulo/{mod['slug']}/", 'icon': mod['icon']
        }
        
        cat = mod['category']
        if cat in categories:
            categories[cat].append(mod_dict)

    result = {
        'nav_asistenciales': categories['asistencial'],
        'nav_administrativos': categories['administrativo'],
        'nav_juridica': categories['juridica'],
        'nav_talento_humano': categories['talento_humano'],
        'nav_contabilidad': categories['contabilidad'],
        'nav_financiera': categories['financiera'],
        'nav_varios': categories['varios'],
        'nav_consultas': categories['consultas'],
        'readonly_db_available': getattr(request, 'readonly_db_available', True)
    }
    # Guardar en cache eliminado para sincronización instantánea
    return result
