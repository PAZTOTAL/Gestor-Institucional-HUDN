from django.core.cache import cache
from .models import DashboardModule


def modules_processor(request):
    """Provides navigation modules to every template. Results are cached."""
    
    # Cache modules for 10 minutes (they rarely change)
    cache_key = 'dashboard_modules_nav'
    cached = cache.get(cache_key)
    
    if cached is None:
        # Fetch active modules from database - single query with only needed fields
        all_modules = list(
            DashboardModule.objects.filter(is_active=True)
            .values('name', 'slug', 'description', 'url', 'icon', 'category')
            .order_by('order', 'name')
        )
        
        asistenciales = []
        administrativos = []
        juridica = []
        talento_humano = []
        financiera = []
        varios = []
        consultas = []
        
        for mod in all_modules:
            mod_dict = {
                'name': mod['name'],
                'slug': mod['slug'],
                'description': mod['description'],
                'url': mod['url'],
                'icon': mod['icon']
            }
            
            cat = mod['category']
            if cat == 'asistencial':
                asistenciales.append(mod_dict)
            elif cat == 'administrativo':
                administrativos.append(mod_dict)
            elif cat == 'juridica':
                juridica.append(mod_dict)
            elif cat == 'talento_humano':
                talento_humano.append(mod_dict)
            elif cat == 'financiera':
                financiera.append(mod_dict)
            elif cat == 'varios':
                varios.append(mod_dict)
            elif cat == 'consultas':
                consultas.append(mod_dict)

        cached = {
            'nav_asistenciales': asistenciales,
            'nav_administrativos': administrativos,
            'nav_juridica': juridica,
            'nav_talento_humano': talento_humano,
            'nav_financiera': financiera,
            'nav_varios': varios,
            'nav_consultas': consultas,
        }
        cache.set(cache_key, cached, 600)  # 10 minutes
    
    result = dict(cached)
    result['readonly_db_available'] = getattr(request, 'readonly_db_available', True)
    return result
