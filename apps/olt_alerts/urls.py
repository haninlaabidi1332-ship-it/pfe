from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertPolicyViewSet, ActiveAlertViewSet, NotificationChannelViewSet

router = DefaultRouter()
router.register(r'policies', AlertPolicyViewSet)
router.register(r'active', ActiveAlertViewSet)
router.register(r'channels', NotificationChannelViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 