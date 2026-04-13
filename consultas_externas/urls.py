from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='consultas_externas_index'),
    path('stats/', views.table_stats, name='table_stats'),
    path('view/<str:model_name>/', views.view_data, name='view_data'),
    path('export/<str:model_name>/', views.export_users_csv, name='export_csv'),
]
