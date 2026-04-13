from .models import DashboardModule

def modules_processor(request):
    # Fetch active modules from database
    all_modules = DashboardModule.objects.filter(is_active=True)
    
    asistenciales = []
    administrativos = []
    varios = []
    consultas = []
    
    for mod in all_modules:
        mod_dict = {
            'name': mod.name,
            'slug': mod.slug,
            'description': mod.description,
            'url': mod.url,
            'icon': mod.icon
        }
        
        if mod.category == 'asistencial':
            asistenciales.append(mod_dict)
        elif mod.category == 'administrativo':
            administrativos.append(mod_dict)
        elif mod.category == 'varios':
            varios.append(mod_dict)
        elif mod.category == 'consultas':
            consultas.append(mod_dict)
        elif mod.category == 'talento_humano':
            # Optionally group with administrative or keep separate if template supports it
            administrativos.append(mod_dict)

    return {
        'nav_asistenciales': asistenciales,
        'nav_administrativos': administrativos,
        'nav_varios': varios,
        'nav_consultas': consultas,
        'readonly_db_available': getattr(request, 'readonly_db_available', True)
    }
