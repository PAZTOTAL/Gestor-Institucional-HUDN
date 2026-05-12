from django.urls import path
from .views import (
    CertificadosDashboardView, generar_certificado_ingresos, 
    LoginRapidoView, solicitar_certificado_email, 
    ListarSolicitudesEmailView, marcar_procesado_email
)

app_name = 'certificados_dian'

urlpatterns = [
    path('acceso-rapido/', LoginRapidoView.as_view(), name='login_rapido'),
    path('', CertificadosDashboardView.as_view(), name='dashboard'),
    path('generar-ingresos/', generar_certificado_ingresos, name='generar_ingresos'),
    path('enviar-email/', solicitar_certificado_email, name='solicitar_email'),
    path('solicitudes/', ListarSolicitudesEmailView.as_view(), name='lista_solicitudes'),
    path('solicitudes/marcar/<int:pk>/', marcar_procesado_email, name='marcar_procesado'),
]
