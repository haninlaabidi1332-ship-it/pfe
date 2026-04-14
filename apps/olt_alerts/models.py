from django.db import models
from apps.olt_inventory.models import Device
from django.conf import settings

class AlertPolicy(models.Model):
    """Définit les règles d'alerte (ex: Seuil de température)"""
    name = models.CharField(max_length=100)
    metric_name = models.CharField(max_length=50) # ex: cpu_usage
    threshold = models.FloatField()
    comparison = models.CharField(max_length=10, choices=[('>', 'Supérieur'), ('<', 'Inférieur')])
    severity = models.CharField(max_length=20, choices=[('critical', 'Critical'), ('warning', 'Warning')])
    is_active = models.BooleanField(default=True)

class ActiveAlert(models.Model):
    """Alertes actuellement non résolues"""
    olt = models.ForeignKey(Device, on_delete=models.CASCADE)
    policy = models.ForeignKey(AlertPolicy, on_delete=models.CASCADE)
    current_value = models.CharField(max_length=100)
    start_time = models.DateTimeField(auto_now_add=True)

class NotificationChannel(models.Model):
    """Canaux de réception (Email, Telegram, etc.)"""
    CHANNEL_TYPES = [('email', 'Email'), ('sms', 'SMS'), ('webhook', 'Webhook')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    destination = models.CharField(max_length=255) # ex: adresse email ou n° tel
    enabled = models.BooleanField(default=True)