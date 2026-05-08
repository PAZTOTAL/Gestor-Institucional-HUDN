"""
URL configuration for the crueremisiones app.
"""

from django.urls import path

from . import views

app_name = 'crueremisiones'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.main_view, name='main'),
    path('remisiones/nueva/', views.remision_create, name='remision_create'),
    path('remisiones/<int:pk>/detalle/', views.remision_detail, name='remision_detail'),
    path('remisiones/<int:pk>/editar/', views.remision_update, name='remision_update'),
    path('remisiones/<int:pk>/eliminar/', views.remision_delete, name='remision_delete'),
    path('exportar/excel/', views.exportar_excel, name='exportar_excel'),
    path('importar/excel/', views.importar_excel, name='importar_excel'),
    path('importar/excel/hojas/', views.importar_excel_hojas, name='importar_excel_hojas'),
    path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
]
