"""
URL configuration for the remisiones app.
"""

from django.urls import path

from . import views

app_name = 'remisiones'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar-password/', views.recuperar_password_view, name='recuperar_password'),
    path('', views.main_view, name='main'),
    path('remisiones/nueva/', views.remision_create, name='remision_create'),
    path('remisiones/<int:pk>/detalle/', views.remision_detail, name='remision_detail'),
    path('remisiones/<int:pk>/editar/', views.remision_update, name='remision_update'),
    path('remisiones/<int:pk>/eliminar/', views.remision_delete, name='remision_delete'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('importar/excel/', views.importar_excel, name='importar_excel'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('usuarios/<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/<int:pk>/cambiar-password/', views.usuario_cambiar_password, name='usuario_cambiar_password'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_delete, name='usuario_delete'),
    path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
]
