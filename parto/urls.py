from django.urls import path, include
from . import views

urlpatterns = [
    # Vista principal (Panel de Control)
    path('', views.index, name='parto_home'),
    path('v2/', views.formulario_v2, name='parto_v2'),
    
    # API endpoints (incluyendo el router de DRF)
    path('api/', include('parto.api_urls')),
    
    # Endpoints de PDF
    path('formulario/<int:formulario_id>/pdf/', views.generar_pdf_formulario, name='generar_pdf_formulario'),
    path('formulario/<int:formulario_id>/impresion/', views.vista_impresion_formulario, name='vista_impresion_formulario'),
    path('pacientes/<int:paciente_id>/pdf/', views.generar_pdf_paciente, name='generar_pdf_paciente'),
    path('pacientes/<int:paciente_id>/preview/', views.preview_pdf_paciente, name='preview_pdf_paciente'),
    
    # API endpoints para búsqueda
    path('api/pacientes-activos/', views.api_buscar_pacientes_activos, name='api_buscar_pacientes_activos'),
    path('api/paciente-detalle/', views.api_buscar_paciente_detalle, name='api_buscar_paciente_detalle'),
]
