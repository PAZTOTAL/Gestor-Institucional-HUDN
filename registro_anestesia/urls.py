from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.list_registros, name='list_registros'),
    path('api/recent-patients/', views.api_recent_patients, name='api_recent_patients'),
    path('create/', views.create_registro, name='create_registro'),
    path('update/<int:pk>/', views.update_registro, name='update_registro'),
    path('print/<int:pk>/', views.print_registro_pdf, name='print_registro_pdf'),
]
