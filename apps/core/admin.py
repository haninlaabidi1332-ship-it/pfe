# apps/core/admin.py
"""
Core Admin - Configuration de la plateforme OLT Supervision
"""
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
import json

from .models import Config


# ============================================================================
# RESSOURCE POUR IMPORT/EXPORT
# ============================================================================

class ConfigResource(resources.ModelResource):
    """Resource pour l'import/export des configurations OLT Supervision"""
    
    class Meta:
        model = Config
        fields = ('id', 'key', 'config_type', 'is_encrypted', 'created_at', 'updated_at')
        export_order = fields


# ============================================================================
# ADMIN DE LA CONFIGURATION
# ============================================================================

@admin.register(Config)
class ConfigAdmin(ImportExportModelAdmin):
    """
    Administration des configurations globales OLT Supervision
    """
    resource_class = ConfigResource
    
    # Liste
    list_display = [
        'key_display', 'config_type_badge', 'value_preview', 
        'encrypted_indicator', 'created_at'
    ]
    list_display_links = ['key_display']
    
    # Filtres
    list_filter = ['config_type', 'is_encrypted', 'created_at']
    
    # Recherche
    search_fields = ['key', 'description', 'value']
    
    # Organisation
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    
    # Champs
    fieldsets = (
        ('⚙️ Configuration OLT', {
            'fields': ('key', 'config_type', 'description')
        }),
        ('📊 Valeur', {
            'fields': ('value',),
            'description': '''
                <div class="alert alert-info">
                    <strong>Format JSON:</strong> La valeur doit être au format JSON valide.
                    <br><strong>Exemples OLT:</strong> 
                    <code>{"snmp_timeout": 5, "snmp_retries": 2}</code>, 
                    <code>{"cpu_threshold": 85, "temperature_threshold": 75}</code>, 
                    <code>42</code>, 
                    <code>"default_community"</code>
                </div>
            '''
        }),
        ('🔒 Sécurité', {
            'fields': ('is_encrypted',),
            'classes': ('collapse',)
        }),
        ('📈 Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'value_formatted']
    
    # ========================================================================
    # MÉTHODES D'AFFICHAGE
    # ========================================================================
    
    def key_display(self, obj):
        """Affiche la clé avec un formatage spécial selon le type OLT"""
        icons = {
            'general': '⚙️',
            'security': '🛡️',
            'snmp': '📡',
            'monitoring': '📊',
            'alerts': '⚠️',
            'notifications': '🔔',
            'integrations': '🔌',
            'thresholds': '📈',
            'scheduling': '⏰',
            'logging': '📝',
        }
        icon = icons.get(obj.config_type, '🔧')
        return format_html(
            '<strong>{} {}</strong><br><small class="text-muted">{}</small>',
            icon, obj.key, obj.description[:50] + '...' if obj.description else ''
        )
    key_display.short_description = 'Configuration'
    key_display.admin_order_field = 'key'
    
    def config_type_badge(self, obj):
        """Badge pour le type de configuration avec couleurs adaptées"""
        colors = {
            'general': 'secondary',
            'security': 'danger',
            'snmp': 'primary',
            'monitoring': 'info',
            'alerts': 'warning',
            'notifications': 'success',
            'integrations': 'dark',
            'thresholds': 'danger',
            'scheduling': 'info',
            'logging': 'secondary',
        }
        color = colors.get(obj.config_type, 'secondary')
        
        type_labels = {
            'general': 'Général',
            'security': 'Sécurité',
            'snmp': 'SNMP',
            'monitoring': 'Monitoring',
            'alerts': 'Alertes',
            'notifications': 'Notifications',
            'integrations': 'Intégrations',
            'thresholds': 'Seuils',
            'scheduling': 'Planification',
            'logging': 'Journalisation',
        }
        label = type_labels.get(obj.config_type, obj.get_config_type_display())
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, label
        )
    config_type_badge.short_description = 'Type'
    config_type_badge.admin_order_field = 'config_type'
    
    def value_preview(self, obj):
        """Aperçu de la valeur"""
        try:
            if isinstance(obj.value, dict):
                keys = list(obj.value.keys())
                if len(keys) > 3:
                    preview = ', '.join(keys[:3]) + f' +{len(keys)-3}'
                else:
                    preview = ', '.join(keys)
                return f"{{ {preview} }}"
            elif isinstance(obj.value, list):
                return f"[{len(obj.value)} éléments]"
            else:
                value_str = str(obj.value)
                if len(value_str) > 50:
                    return value_str[:50] + '...'
                return value_str
        except:
            return '⚠️ Erreur de format'
    value_preview.short_description = 'Valeur'
    
    def encrypted_indicator(self, obj):
        """Indicateur de chiffrement"""
        if obj.is_encrypted:
            return format_html('<span class="badge bg-warning" title="Donnée chiffrée">🔒 Chiffré</span>')
        return format_html('<span class="badge bg-success" title="Donnée en clair">🔓 Clair</span>')
    encrypted_indicator.short_description = 'Sécurité'
    
    def value_formatted(self, obj):
        """Affiche la valeur formatée en JSON"""
        try:
            if isinstance(obj.value, (dict, list)):
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px;">{}</pre>',
                    json.dumps(obj.value, indent=2, ensure_ascii=False)
                )
            else:
                return format_html(
                    '<code>{}</code>',
                    obj.value
                )
        except:
            return format_html(
                '<span class="text-danger">Erreur de format JSON</span>'
            )
    value_formatted.short_description = 'Valeur (formatée)'
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def save_model(self, request, obj, form, change):
        """Validation avant sauvegarde avec règles OLT"""
        try:
            # S'assurer que la valeur est un JSON valide
            if isinstance(obj.value, str):
                try:
                    obj.value = json.loads(obj.value)
                except json.JSONDecodeError:
                    pass
            
            # Validation spécifique selon le type
            if obj.config_type == 'snmp' and isinstance(obj.value, dict):
                if 'timeout' in obj.value and not isinstance(obj.value['timeout'], (int, float)):
                    raise ValueError("Le timeout SNMP doit être un nombre")
                if 'retries' in obj.value and not isinstance(obj.value['retries'], int):
                    raise ValueError("Le nombre de tentatives SNMP doit être un entier")
            
            elif obj.config_type == 'thresholds' and isinstance(obj.value, dict):
                if 'cpu' in obj.value and not isinstance(obj.value['cpu'], (int, float)):
                    raise ValueError("Le seuil CPU doit être un nombre")
                if obj.value.get('cpu', 0) < 0 or obj.value.get('cpu', 0) > 100:
                    raise ValueError("Le seuil CPU doit être compris entre 0 et 100")
            
            elif obj.config_type == 'monitoring' and isinstance(obj.value, dict):
                if 'collection_interval' in obj.value and not isinstance(obj.value['collection_interval'], int):
                    raise ValueError("L'intervalle de collecte doit être un entier")
                if obj.value.get('collection_interval', 0) < 10:
                    raise ValueError("L'intervalle de collecte doit être au moins 10 secondes")
            
            super().save_model(request, obj, form, change)
            
            action = 'modifiée' if change else 'créée'
            self.message_user(
                request, 
                f'✅ Configuration "{obj.key}" {action} avec succès.',
                messages.SUCCESS
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'❌ Erreur: {str(e)}',
                messages.ERROR
            )
    
    # ========================================================================
    # ACTIONS PERSONNALISÉES
    # ========================================================================
    
    actions = ['duplicate_config', 'export_selected', 'toggle_encryption', 'validate_configs']
    
    def duplicate_config(self, request, queryset):
        """Duplique une configuration"""
        for config in queryset:
            new_key = f"{config.key}_copie"
            count = 1
            while Config.objects.filter(key=new_key).exists():
                count += 1
                new_key = f"{config.key}_copie_{count}"
            
            Config.objects.create(
                key=new_key,
                value=config.value,
                description=f"Copie de {config.key}",
                config_type=config.config_type,
                is_encrypted=config.is_encrypted
            )
        
        self.message_user(
            request,
            f'✅ {queryset.count()} configuration(s) dupliquée(s).',
            messages.SUCCESS
        )
    duplicate_config.short_description = "📋 Dupliquer la sélection"
    
    def export_selected(self, request, queryset):
        """Export JSON des configurations sélectionnées"""
        from django.http import HttpResponse
        
        data = []
        for config in queryset:
            data.append({
                'key': config.key,
                'value': config.value,
                'description': config.description,
                'config_type': config.config_type,
                'config_type_display': config.get_config_type_display(),
                'is_encrypted': config.is_encrypted,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None,
            })
        
        response = HttpResponse(
            json.dumps(data, indent=2, default=str, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="olt_configurations.json"'
        return response
    export_selected.short_description = "📤 Exporter la sélection"
    
    def toggle_encryption(self, request, queryset):
        """Active/désactive le chiffrement"""
        count = 0
        for config in queryset:
            config.is_encrypted = not config.is_encrypted
            config.save()
            count += 1
        
        self.message_user(
            request,
            f'🔄 Statut de chiffrement modifié pour {count} configuration(s).',
            messages.SUCCESS
        )
    toggle_encryption.short_description = "🔄 Basculer chiffrement"
    
    def validate_configs(self, request, queryset):
        """Valide les configurations sélectionnées"""
        errors = []
        warnings = []
        
        for config in queryset:
            if config.config_type == 'snmp' and isinstance(config.value, dict):
                if 'timeout' in config.value and not isinstance(config.value['timeout'], (int, float)):
                    errors.append(f"{config.key}: timeout doit être un nombre")
                if 'retries' in config.value and not isinstance(config.value['retries'], int):
                    errors.append(f"{config.key}: retries doit être un entier")
            
            elif config.config_type == 'thresholds' and isinstance(config.value, dict):
                if 'cpu' in config.value and (not isinstance(config.value['cpu'], (int, float)) or config.value['cpu'] < 0 or config.value['cpu'] > 100):
                    errors.append(f"{config.key}: cpu doit être un nombre entre 0 et 100")
                if 'temperature' in config.value and not isinstance(config.value['temperature'], (int, float)):
                    errors.append(f"{config.key}: temperature doit être un nombre")
            
            elif config.config_type == 'monitoring' and isinstance(config.value, dict):
                if 'collection_interval' in config.value and (not isinstance(config.value['collection_interval'], int) or config.value['collection_interval'] < 10):
                    errors.append(f"{config.key}: collection_interval doit être un entier >= 10")
        
        if errors:
            self.message_user(
                request,
                f'❌ Erreurs:\n' + '\n'.join(errors),
                messages.ERROR
            )
        elif warnings:
            self.message_user(
                request,
                f'⚠️ Avertissements:\n' + '\n'.join(warnings),
                messages.WARNING
            )
        else:
            self.message_user(
                request,
                f'✅ Toutes les configurations sont valides.',
                messages.SUCCESS
            )
    validate_configs.short_description = "✅ Valider la sélection"
    
    # ========================================================================
    # PERMISSIONS
    # ========================================================================
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly.append('key')
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        critical_keys = [
            'platform.version',
            'platform.secret_key',
            'database.config',
            'security.master_key',
            'api.secret',
            'encryption.key',
            'snmp.default_community',
            'snmp.timeout',
            'thresholds.default_cpu',
            'thresholds.default_temperature',
            'monitoring.collection_interval',
            'alerts.cooldown_minutes',
        ]
        if obj and obj.key in critical_keys:
            return False
        return super().has_delete_permission(request, obj)


# ============================================================================
# CONFIGURATION DU DASHBOARD CORE
# ============================================================================

class CoreDashboard:
    """
    Statistiques pour le dashboard core OLT Supervision
    """
    
    @staticmethod
    def get_stats():
        """Récupère les statistiques des configurations OLT"""
        total_configs = Config.objects.count()
        
        configs_by_type = {}
        type_labels = {
            'general': 'Général',
            'security': 'Sécurité',
            'snmp': 'SNMP',
            'monitoring': 'Monitoring',
            'alerts': 'Alertes',
            'notifications': 'Notifications',
            'integrations': 'Intégrations',
            'thresholds': 'Seuils',
            'scheduling': 'Planification',
            'logging': 'Journalisation',
        }
        
        for config_type, _ in Config.CONFIG_TYPES:
            count = Config.objects.filter(config_type=config_type).count()
            if count > 0:
                label = type_labels.get(config_type, config_type)
                configs_by_type[label] = count
        
        encrypted_count = Config.objects.filter(is_encrypted=True).count()
        
        return {
            'total_configs': total_configs,
            'total_configs_display': f'{total_configs} configuration(s) OLT',
            'configs_by_type': configs_by_type,
            'encrypted_count': encrypted_count,
            'encrypted_percentage': round((encrypted_count / total_configs * 100) if total_configs > 0 else 0, 1),
        }


# Configuration de l'interface d'administration
admin.site.site_header = "OLT Supervision - Administration"
admin.site.site_title = "OLT Supervision Admin"
admin.site.index_title = "📊 Tableau de bord OLT Supervision"
