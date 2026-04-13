from django.urls import path
from . import views

app_name = 'consentimientos'

urlpatterns = [
    path('', views.ConsentimientoListView.as_view(), name='list'),
    path('crear/<int:template_id>/', views.ConsentimientoCreateView.as_view(), name='create'),
    path('detalle/<int:pk>/', views.ConsentimientoDetailView.as_view(), name='detail'),
    
    # Plantillas (Administración)
    path('plantilla/nueva/', views.TemplateCreateView.as_view(), name='template_create'),
    path('plantilla/editar/<int:pk>/', views.TemplateUpdateView.as_view(), name='template_update'),
    
    # API para búsqueda de pacientes (si es necesario un modal similar al de registros)
    path('api/buscar-pacientes/', views.buscar_pacientes, name='api_buscar_pacientes'),
]
