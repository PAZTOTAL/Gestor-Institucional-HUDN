from django.urls import path, re_path
from . import views

app_name = 'visor_soportes'

urlpatterns = [
    path("api/health", views.health, name='health'),
    path("api/consulta/contratos/<str:identificacion>", views.contratos, name='api_contratos'),
    path("api/consulta/documentos/<int:ide_contratista_int>", views.documentos, name='api_documentos'),
    path("api/consulta/documento", views.documento, name='api_documento'),
    path("api/consulta/documento", views.documento, name='api_documento'),
    path("", views.index, name='index'),
    re_path(r"^(?!api/).*$", views.index),
]
