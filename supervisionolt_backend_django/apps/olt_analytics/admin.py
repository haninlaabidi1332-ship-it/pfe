from django.contrib import admin
from .models import NetworkReport, AlertHistory

@admin.register(NetworkReport)
class NetworkReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_at', 'availability_score', 'total_traffic_gb')
    list_filter = ('report_type',)

@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = ('olt', 'severity', 'alert_type', 'is_resolved', 'created_at')
    list_filter = ('severity', 'is_resolved', 'olt')
    search_fields = ('message', 'alert_type')