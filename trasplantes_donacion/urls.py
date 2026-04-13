from django.urls import path
from . import views

app_name = 'trasplantes_donacion'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('alertas/', views.AlertasView.as_view(), name='alertas'),
    path('sync/', views.sync_excel, name='sync'),
    path('sync-husn/', views.sync_husn, name='sync_husn'),
]
