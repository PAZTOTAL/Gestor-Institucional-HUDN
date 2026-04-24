from django.urls import path
from . import views

app_name = 'tercerizadas'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # AJAX
    path('ajax/buscar-dinamica/', views.buscar_en_dinamica, name='buscar_dinamica'),

    # Servidores
    path('servidores/', views.lista_servidores, name='lista_servidores'),
    path('servidores/nuevo/', views.crear_servidor, name='crear_servidor'),
    path('servidores/<int:pk>/', views.detalle_servidor, name='detalle_servidor'),
    path('servidores/<int:pk>/editar/', views.editar_servidor, name='editar_servidor'),

    # Empresas
    path('empresas/', views.lista_empresas, name='lista_empresas'),
    path('empresas/nueva/', views.crear_empresa, name='crear_empresa'),
    path('empresas/<int:pk>/editar/', views.editar_empresa, name='editar_empresa'),

    # Asignaciones y Afiliaciones
    path('servidores/<int:servidor_pk>/asignacion/', views.agregar_asignacion, name='agregar_asignacion'),
    path('servidores/<int:servidor_pk>/afiliacion/', views.agregar_afiliacion, name='agregar_afiliacion'),
]
