from django.urls import path
from .views import HomeView, ModuleDetailView, TableDetailView, DynamicCreateView, DynamicUpdateView, DynamicDeleteView, DynamicExcelTemplateView, DynamicImportExcelView, VariosPanelView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('varios/', VariosPanelView.as_view(), name='varios_panel'),
    path('modulo/<str:module_name>/', ModuleDetailView.as_view(), name='module_detail'),
    path('modulo/<str:module_name>/tabla/<str:model_name>/', TableDetailView.as_view(), name='table_detail'),
    path('modulo/<str:module_name>/tabla/<str:model_name>/crear/', DynamicCreateView.as_view(), name='table_create'),
    path('modulo/<str:module_name>/tabla/<str:model_name>/editar/<str:pk>/', DynamicUpdateView.as_view(), name='table_update'),
    path('modulo/<str:module_name>/tabla/<str:model_name>/borrar/<str:pk>/', DynamicDeleteView.as_view(), name='table_delete'),
    path('modulo/<str:module_name>/tabla/<str:model_name>/plantilla/', DynamicExcelTemplateView.as_view(), name='table_template'),
    path('modulo/<str:module_name>/tabla/<str:model_name>/importar/', DynamicImportExcelView.as_view(), name='table_import'),
]
