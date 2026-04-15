from django.contrib import admin
from .models import AlertPolicy, ActiveAlert, NotificationChannel

@admin.register(AlertPolicy)
class AlertPolicyAdmin(admin.ModelAdmin):
    # Affiche les règles de manière claire
    list_display = ('name', 'metric_name', 'comparison', 'threshold', 'severity', 'is_active')
    # Permet de filtrer par sévérité ou état (Actif/Inactif)
    list_filter = ('severity', 'is_active', 'metric_name')
    # Permet de rechercher par nom de règle
    search_fields = ('name', 'metric_name')
    # Permet d'activer/désactiver une règle directement depuis la liste
    list_editable = ('is_active',)

@admin.register(ActiveAlert)
class ActiveAlertAdmin(admin.ModelAdmin):
    # Affiche les alertes qui brûlent en ce moment
    list_display = ('olt', 'policy', 'current_value', 'start_time')
    list_filter = ('policy__severity', 'olt')
    # On met les champs en lecture seule car une alerte active est générée par le système
    readonly_fields = ('start_time',)

@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    # Gère qui reçoit les alertes
    list_display = ('user', 'channel_type', 'destination', 'enabled')
    list_filter = ('channel_type', 'enabled')
    search_fields = ('user__username', 'destination')