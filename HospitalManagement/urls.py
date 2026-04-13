"""
URL configuration for HospitalManagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from .api_views import query_tercero, get_tercero_details, query_paciente_enhanced, get_diagnostico_paciente

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/lookup-tercero/', query_tercero, name='api_lookup_tercero'),
    path('api/lookup-paciente-enhanced/', query_paciente_enhanced, name='api_lookup_paciente_enhanced'),
    path('api/tercero-details/<int:oid>/', get_tercero_details, name='api_tercero_details'),
    path('api/paciente-ultimo-diagnostico/<int:oid>/', get_diagnostico_paciente, name='api_paciente_ultimo_diagnostico'),
    path('', include('core.urls')),
    path('', include('usuarios.urls')),
    path('consultas-externas/', include('consultas_externas.urls')),
    path('registro-anestesia/', include('registro_anestesia.urls')),
    path('meows/', include('meows.urls')),  # Sistema MEOWS
    path('parto/', include('parto.urls')),  # Sistema Parto
    path('consultas/', include('consultas.urls')),
    path('presupuesto/', include('presupuesto.urls')),
    path('consentimientos/', include('ConsentimientosInformados.urls')),
    path('consentimientos-v2/', include('consentimientos.urls')),
    path('central-mezclas/', include('CentralDeMezclas.urls')),
    path('estudio-conveniencia/', include('EstudioDeConveniencia.urls')),
    path('trasplantes-donacion/', include('trasplantes_donacion.urls')),
    path('certificados-dian/', include('CertificadosDIAN.urls')),
    path('horas-extras/', include('horas_extras.urls')),
]
