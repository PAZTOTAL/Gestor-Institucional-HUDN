from django.urls import path
from .views import (
    FRQUI_095_CreateView, FRQUI_095_ListView, generar_pdf_frqui_095, FRQUI_095_UpdateView,
    FRQUI_001_CreateView, FRQUI_001_ListView, FRQUI_001_UpdateView, generar_pdf_frqui_001
)

app_name = 'formatos_apps'

urlpatterns = [
    # FRQUI-095
    path('frqui-095/', FRQUI_095_ListView.as_view(), name='frqui_095_list'),
    path('frqui-095/nuevo/', FRQUI_095_CreateView.as_view(), name='frqui_095_create'),
    path('frqui-095/editar/<int:pk>/', FRQUI_095_UpdateView.as_view(), name='frqui_095_update'),
    path('frqui-095/pdf/<int:pk>/', generar_pdf_frqui_095, name='frqui_095_pdf'),

    # FRQUI-001
    path('frqui-001/', FRQUI_001_ListView.as_view(), name='frqui_001_list'),
    path('frqui-001/nuevo/', FRQUI_001_CreateView.as_view(), name='frqui_001_create'),
    path('frqui-001/editar/<int:pk>/', FRQUI_001_UpdateView.as_view(), name='frqui_001_update'),
    path('frqui-001/pdf/<int:pk>/', generar_pdf_frqui_001, name='frqui_001_pdf'),
]
