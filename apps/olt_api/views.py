from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class APIRootView(APIView):
    """Vue d'accueil qui liste tous les modules disponibles"""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "message": "Bienvenue sur l'API de gestion OLT v1",
            "modules": {
                "inventory": "/api/v1/inventory/",
                "monitoring": "/api/v1/monitoring/",
                "alerts": "/api/v1/alerts/",
                "analytics": "/api/v1/analytics/",
                "dashboard": "/api/v1/dashboard/"
            },
            "status": "Running"
        })