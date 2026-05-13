from django.urls import path, include

urlpatterns = [
    path('', include('unificador_v1.urls.base')),
    path('meows/', include('unificador_v1.urls.meows')),
    path('parto/', include('unificador_v1.urls.parto')),
    path('fetal/', include('unificador_v1.urls.fetal')),
]
