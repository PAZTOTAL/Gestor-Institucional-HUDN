from django.urls import path
from . import views

app_name = 'organigrama'

urlpatterns = [
    path('', views.OrganigramaDashboardView.as_view(), name='dashboard'),
]
