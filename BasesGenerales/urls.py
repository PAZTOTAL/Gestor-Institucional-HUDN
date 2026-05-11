from django.urls import path
from . import views

app_name = 'georeferencia'

urlpatterns = [
    path('', views.GeoreferenciaDashboardView.as_view(), name='dashboard'),
]
