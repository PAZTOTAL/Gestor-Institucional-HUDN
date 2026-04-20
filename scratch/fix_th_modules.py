from core.models import DashboardModule

def update_modules():
    # 1. Informe de Consistencia (Excel vs Dinámica)
    cons, created = DashboardModule.objects.get_or_create(slug='th_consistencia_excel')
    cons.name = 'Conciliación Nómina vs Excel'
    cons.category = 'talento_humano'
    cons.description = 'Cruce de información entre Dinámica y el Excel Maestro de Cargos'
    cons.url = '/horas-extras/informes/consistencia-excel/'
    cons.icon = 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'
    cons.is_active = True
    cons.order = 5
    cons.save()
    print(f"Updated {cons.name}")

if __name__ == '__main__':
    update_modules()
