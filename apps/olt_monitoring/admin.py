from django.contrib import admin
from .models import SNMPMetric, BFDSession, PerformanceMetric

@admin.register(SNMPMetric)
class SNMPMetricAdmin(admin.ModelAdmin):
    # Ce qui sera affiché dans la liste
    list_display = ('olt', 'metric_name', 'metric_value_numeric', 'unit', 'timestamp')
    # Les filtres sur le côté droit
    list_filter = ('olt', 'metric_name', 'timestamp')
    # Barre de recherche
    search_fields = ('metric_name', 'interface_name', 'oid')
    # Tri par défaut (le plus récent en premier)
    ordering = ('-timestamp',)

@admin.register(BFDSession)
class BFDSessionAdmin(admin.ModelAdmin):
    list_display = ('olt', 'interface', 'session_state', 'last_up_time', 'last_down_time')
    list_filter = ('session_state', 'olt')
    # Permet de colorer l'état UP/DOWN pour que ce soit plus visuel
    list_editable = ('session_state',) 

@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ('olt', 'metric_type', 'value', 'unit', 'timestamp')
    list_filter = ('metric_type', 'olt', 'timestamp')
    search_fields = ('metric_type',)