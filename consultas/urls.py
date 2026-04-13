from django.urls import path
from . import views

app_name = 'consultas'

urlpatterns = [
    path('admin/', views.dashboard_admin, name='dashboard_admin'),
    path('salud/', views.dashboard_salud, name='dashboard_salud'),
    path('aseguradoras/', views.dashboard_aseguradoras, name='dashboard_aseguradoras'),
    path('exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('informes-rips/', views.informes_rips, name='informes_rips'),
    path('generar-rips/', views.generar_rips, name='generar_rips'),
    path('produccion-medico/', views.produccion_medico, name='produccion_medico'),
    path('produccion-medico/excel/', views.produccion_medico_excel, name='produccion_medico_excel'),
    # Patient Tracking
    path('pacientes-urgencias/', views.pacientes_urgencias_list, name='pacientes_urgencias_list'),
    path('paciente/<int:ingreso_id>/', views.paciente_detalle, name='paciente_detalle'),
    path('paciente-historial/', views.paciente_historial, name='paciente_historial_search'),
    path('paciente-historial/<str:documento>/', views.paciente_historial, name='paciente_historial'),
]
