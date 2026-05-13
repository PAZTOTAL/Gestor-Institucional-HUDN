"""
URLs del sistema obstétrico.
Punto de entrada: http://127.0.0.1:8000/ → redirige a /atencion/ (dashboard)

Estructura robusta: cada módulo tiene prefijo explícito, sin path('', ...) ambiguos.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.shortcuts import redirect
from unificador_v1.models import AtencionParto


def home(request):
    """Raíz / → redirige SIEMPRE a /atencion/ (dashboard)."""
    return redirect("/atencion/")


from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.svg', permanent=True)),
    path('admin/', admin.site.urls),
    path('login/', RedirectView.as_view(url='/', permanent=False)),
    path('accounts/login/', RedirectView.as_view(url='/', permanent=False)),
    path('api/', include('unificador_v1.urls.parto')), # Redirigido a unificador_v1

    # Módulos con prefijos explícitos (evita conflictos de rutas)
    # Módulos con prefijos explícitos (Consolidados en unificador_v1)
    path('meows/', include('unificador_v1.urls.meows')),
    path('fetal/', include('unificador_v1.urls.fetal')),
    path('parto/', include('unificador_v1.urls.parto')),
    path('atencion/', include('unificador_v1.urls.base')),

    # Raíz: ÚNICA ruta que captura / → redirige a /atencion/1/
    path('', home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


