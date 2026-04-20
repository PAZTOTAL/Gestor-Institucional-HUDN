from django.core.cache import cache
from .models import DashboardModule
from usuarios.models import PermisoApp


def modules_processor(request):
    """Provides navigation modules filtered by user permissions."""
    
    # 1. Fetch all active modules (cached globally)
    # Reduced cache time to 60 seconds for faster updates
    cache_key_all = 'all_active_dashboard_modules'
    all_modules = cache.get(cache_key_all)
    
    if all_modules is None:
        all_modules = list(
            DashboardModule.objects.filter(is_active=True)
            .values('name', 'slug', 'description', 'url', 'icon', 'category')
            .order_by('order', 'name')
        )
        cache.set(cache_key_all, all_modules, 60)

    # 2. Get User Permissions
    allowed_apps = set()
    is_superuser = False
    
    if request.user.is_authenticated:
        if request.user.is_superuser:
            is_superuser = True
        else:
            # Reutilizar permisos ya procesados en la vista si existen
            allowed_apps = getattr(request, '_allowed_apps', None)
            if allowed_apps is None:
                # Si no están en el request, los calculamos aquí
                raw_perms = set(
                    PermisoApp.objects.filter(user=request.user, permitido=True)
                    .values_list('app_label', flat=True)
                )
                
                # Mapa de Equivalencias
                equiv_map = {
                    'certificados_laborales': 'mvp',
                    'mvp': 'certificados_laborales',
                }
                
                allowed_apps = raw_perms.copy()
                for p in raw_perms:
                    if p in equiv_map:
                        allowed_apps.add(equiv_map[p])

    # 3. Filter and Group Modules
    categories = {
        'asistencial': [],
        'administrativo': [],
        'juridica': [],
        'talento_humano': [],
        'contabilidad': [],
        'financiera': [],
        'varios': [],
        'consultas': []
    }

    for mod in all_modules:
        slug = mod['slug']
        
        has_perm = is_superuser
        if not has_perm:
            # Lógica de Permisos Unificada y Estricta (Relación 1 a 1)
            if slug in allowed_apps:
                has_perm = True
            
        if not has_perm:
            continue

        mod_dict = {
            'name': mod['name'],
            'slug': mod['slug'],
            'description': mod['description'],
            'url': mod['url'],
            'icon': mod['icon']
        }
        
        cat = mod['category']
        if cat in categories:
            categories[cat].append(mod_dict)

    return {
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
