from django.urls import path
from . import views

app_name = 'estudio_conveniencia'

urlpatterns = [
    path('pdf/<int:pk>/', views.GenerarEstudioPDFView.as_view(), name='generar_pdf'),
]
