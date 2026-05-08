from django.urls import path
from .views import DocumentoInventarioListView

urlpatterns = [
    path('documentos/', DocumentoInventarioListView.as_view(), name='inventarios_documentos'),
]
