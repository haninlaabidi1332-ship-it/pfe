# apps/olt_inventory/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# On initialise le router comme dans l'app users
router = DefaultRouter()
router.register('devices', views.DeviceViewSet, basename='device')
router.register('onus', views.ONUViewSet, basename='onu')
router.register('interfaces', views.InterfaceViewSet, basename='interface')

urlpatterns = router.urls