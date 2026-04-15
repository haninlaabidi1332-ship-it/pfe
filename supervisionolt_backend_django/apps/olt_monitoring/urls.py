from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SNMPMetricViewSet, BFDSessionViewSet, PerformanceMetricViewSet

router = DefaultRouter()
router.register(r'snmp-metrics', SNMPMetricViewSet)
router.register(r'bfd-sessions', BFDSessionViewSet)
router.register(r'performance-metrics', PerformanceMetricViewSet)

urlpatterns = [
    path('', include(router.urls)),
]