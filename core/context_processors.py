from django.core.cache import cache
from .models import DashboardModule
from usuarios.models import PermisoApp


def modules_processor(request):
    """Provides navigation modules filtered by user permissions."""
    if not request.user.is_authenticated:
        return {}

    # 1. Intentar obtener el dashboard completo desde cache para este usuario
    cache_key_user = f'user_dashboard_nav_{request.user.id}'
    cached_nav = cache.get(cache_key_user)
    if cached_nav:
        return cached_nav

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
    
    # Mapa de Equivalencias
    equiv_map = {
        'certificados_laborales': 'mvp',
        'mvp': 'certificados_laborales',
        'consultas_externas': 'consultas',
        'consultas': 'consultas_externas',
    }
    
    final_allowed = set(allowed_apps)
    for p in allowed_apps:
        if p in equiv_map:
            final_allowed.add(equiv_map[p])

    # 3. Filter and Group Modules
    categories = {
        'asistencial': [], 'administrativo': [], 'juridica': [], 
        'talento_humano': [], 'contabilidad': [], 'financiera': [], 
        'varios': [], 'consultas': []
    }

    for mod in all_modules:
        slug = mod['slug']
        has_perm = is_superuser
        if not has_perm:
            if slug in final_allowed:
                has_perm = True
            elif slug.startswith('th_') and 'horas_extras' in final_allowed:
                has_perm = True
            elif slug.startswith('CertificadosDIAN') and ('CertificadosDIAN' in final_allowed or 'CertificadosDIAN_SOL' in final_allowed):
                has_perm = True
            elif (slug.startswith('consultas_') or slug == 'produccion-medico') and 'consultas' in final_allowed:
                has_perm = True
            elif (slug.startswith('defenjur_') or slug == 'legal') and 'defenjur' in final_allowed:
                has_perm = True
            
        if not has_perm:
            continue

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
    
    # Guardar en cache por 5 minutos
    cache.set(cache_key_user, result, 300)
    return result
