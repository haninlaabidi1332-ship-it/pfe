from django.urls import path, include
from .views import APIRootView

urlpatterns = [
    # Point d'entrée de l'API
    path('', APIRootView.as_view(), name='api-root'),
    
    # Inclusion de toutes tes autres applications
    path('inventory/', include('apps.olt_inventory.urls')),
    path('monitoring/', include('apps.olt_monitoring.urls')),
    path('analytics/', include('apps.olt_analytics.urls')),
    path('alerts/', include('apps.olt_alerts.urls')),
    path('dashboard/', include('apps.olt_dashboard.urls')),
]