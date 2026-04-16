from django.urls import path
from . import views

app_name = 'certificados_laborales'

urlpatterns = [
    path('', views.certificados_laborales_index, name='index'),
    path('api/consultar-contratos/', views.api_consultar_contratos, name='api_consultar_contratos'),
    path('api/generar-certificado/', views.api_generar_certificado, name='api_generar_certificado'),
]
