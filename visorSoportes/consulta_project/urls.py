from django.urls import path, re_path

from consulta_api import views


urlpatterns = [
    path("api/health", views.health),
    path("api/consulta/contratos/<str:identificacion>", views.contratos),
    path("api/consulta/documentos/<int:ide_contratista_int>", views.documentos),
    path("api/consulta/documento", views.documento),
    path("app.js", views.static_app_js),
    path("styles.css", views.static_styles_css),
    path("assets/pdf-lib.min.js", views.static_pdf_lib),
    path("", views.index),
    re_path(r"^(?!api/).*$", views.index),
]
