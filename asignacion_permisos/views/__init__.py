from rest_framework.views import APIView


class APCAPIView(APIView):
    """Base para vistas API del módulo APC — sin SessionAuthentication para JWT Bearer."""
    authentication_classes = []
