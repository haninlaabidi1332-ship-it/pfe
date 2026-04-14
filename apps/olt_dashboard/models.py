from django.db import models
from django.conf import settings

class UserDashboardConfig(models.Model):
    """Stocke les widgets préférés de l'utilisateur"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    show_critical_alerts = models.BooleanField(default=True)
    refresh_interval = models.IntegerField(default=30) # secondes
    layout_data = models.JSONField(default=dict) # Pour mémoriser l'ordre des graphiques