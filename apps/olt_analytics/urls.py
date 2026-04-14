from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NetworkReportViewSet, AlertHistoryViewSet

router = DefaultRouter()
router.register(r'reports', NetworkReportViewSet)
router.register(r'alerts', AlertHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]