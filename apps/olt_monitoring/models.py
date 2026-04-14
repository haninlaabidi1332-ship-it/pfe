from django.db import models
from apps.olt_inventory.models import Device, Interface



class SNMPMetric(models.Model):
    olt = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='snmp_metrics')
    oid = models.CharField(max_length=255)
    metric_name = models.CharField(max_length=100)
    metric_value = models.CharField(max_length=500)
    metric_value_numeric = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=50)
    interface_index = models.IntegerField(null=True, blank=True)
    interface_name = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    poll_duration_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Métrique SNMP"
        ordering = ['-timestamp']

class BFDSession(models.Model):
    STATE_CHOICES = [('up', 'UP'), ('down', 'DOWN'), ('admin_down', 'Admin Down'), ('init', 'Init')]
    olt = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='bfd_sessions')
    interface = models.ForeignKey(Interface, on_delete=models.SET_NULL, null=True, blank=True)
    session_state = models.CharField(max_length=20, choices=STATE_CHOICES, default='down')
    local_discriminator = models.IntegerField(null=True, blank=True)
    remote_discriminator = models.IntegerField(null=True, blank=True)
    last_up_time = models.DateTimeField(null=True, blank=True)
    last_down_time = models.DateTimeField(null=True, blank=True)

class PerformanceMetric(models.Model):
    olt = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='perf_metrics')
    metric_type = models.CharField(max_length=50)  # latency, jitter, packet_loss
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
     