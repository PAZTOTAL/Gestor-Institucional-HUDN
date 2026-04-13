from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/health", views.health, name="health"),
    path("api/empleados/<str:cedula>", views.empleado_por_cedula, name="empleado_por_cedula"),
    path("api/certificados", views.generar_certificado, name="generar_certificado"),
]
