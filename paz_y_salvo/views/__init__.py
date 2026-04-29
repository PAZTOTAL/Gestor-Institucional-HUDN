from rest_framework.views import APIView


class PysAPIView(APIView):
    """Base para todas las vistas API de Paz y Salvo.
    Sin authentication_classes para evitar que SessionAuthentication
    re-aplique CSRF sobre rutas que usan JWT Bearer token."""
    authentication_classes = []
