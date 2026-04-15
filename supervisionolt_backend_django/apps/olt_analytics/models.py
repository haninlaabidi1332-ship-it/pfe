from django.db import models
from apps.olt_inventory.models import Device

class NetworkReport(models.Model):
    REPORT_TYPES = [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_at = models.DateTimeField(auto_now_add=True)
    total_active_onus = models.IntegerField()
    average_latency = models.FloatField()
    total_traffic_gb = models.FloatField()
    availability_score = models.FloatField(help_text="En pourcentage (ex: 99.9)")

    class Meta:
        ordering = ['-generated_at']

class AlertHistory(models.Model):
    SEVERITY = [('critical', 'Critical'), ('warning', 'Warning'), ('info', 'Info')]
    
    olt = models.ForeignKey(Device, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=100)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)