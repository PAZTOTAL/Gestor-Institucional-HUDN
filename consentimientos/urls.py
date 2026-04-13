from django.urls import path
from . import views

app_name = 'consentimientos_v2'

urlpatterns = [
    path('', views.listar_documentos, name='lista'),
    path('<int:pk>/', views.detalle_documento, name='detalle'),
    
    # Firma de Documento (Signature Pad)
    path('<int:pk>/firmar/', views.guardar_firma_documento, name='guardar_firma'),
    path('firma/<int:pk>/descargar/', views.descargar_pdf_firmado, name='descargar_pdf'),
    # API para Pacientes Activos y Auto-llenado
    path('api/pacientes-activos/', views.api_pacientes_activos, name='api_pacientes_activos'),
    path('api/paciente-data/<int:ingreso_id>/', views.api_paciente_data, name='api_paciente_data'),
    path('api/historial-firmas/', views.api_historial_firmas, name='api_historial_firmas'),
    path('staff/registro-firma/', views.registro_firma_staff, name='registro_firma_staff'),
]
