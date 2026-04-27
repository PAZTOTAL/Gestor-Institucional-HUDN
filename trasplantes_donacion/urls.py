from django.urls import path
from . import views

app_name = 'trasplantes_donacion'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('alertas/', views.AlertasView.as_view(), name='alertas'),
    path('sync/', views.sync_excel, name='sync'),
    path('sync-husn/', views.sync_husn, name='sync_husn'),
    path('historia/<int:pk>/', views.historia_clinica_api, name='historia_clinica'),
    path('editar/<int:pk>/', views.PacienteUpdateView.as_view(), name='editar_proceso'),
    path('reporte-diario/', views.reporte_diario, name='reporte_diario_glasgow'),
    path('reporte-mensual/', views.reporte_mensual, name='reporte_mensual'),
]

