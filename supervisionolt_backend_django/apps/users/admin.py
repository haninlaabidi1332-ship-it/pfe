# apps/users/admin.py
"""
Users Admin - Interface d'administration pour OLT Supervision
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import models
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import DateTimeWidget
import json
from datetime import timedelta

from .models import User, Team, Role, Permission, UserActivity


# ============================================================================
# RESSOURCES POUR IMPORT/EXPORT
# ============================================================================

class UserResource(resources.ModelResource):
    """Resource pour l'import/export des utilisateurs OLT Supervision"""
    
    created_at = fields.Field(attribute='created_at', widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S'))
    last_login = fields.Field(attribute='last_login', widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S'))
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'status', 'department', 'job_title', 'employee_id',
            'phone', 'is_active', 'is_verified', 'two_factor_enabled',
            'api_access_enabled', 'api_rate_limit', 'created_at'
        )
        export_order = fields


class TeamResource(resources.ModelResource):
    """Resource pour l'import/export des équipes OLT"""
    
    created_at = fields.Field(attribute='created_at', widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S'))
    
    class Meta:
        model = Team
        fields = ('id', 'name', 'description', 'team_lead', 'created_at')
        export_order = fields


# ============================================================================
# ADMIN DES UTILISATEURS
# ============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin, ImportExportModelAdmin):
    """
    Administration des utilisateurs OLT Supervision
    """
    resource_class = UserResource
    
    list_display = [
        'email', 'get_full_name', 'role_badge', 'status_badge',
        'security_icons', 'api_status', 'last_activity'
    ]
    list_display_links = ['email']
    
    list_filter = [
        'role', 'status', 'is_active', 'is_verified', 
        'two_factor_enabled', 'api_access_enabled', 'department'
    ]
    
    search_fields = ['email', 'username', 'first_name', 'last_name', 'employee_id']
    
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    
    actions = [
        'activate_users', 'deactivate_users', 'suspend_users', 'unlock_users',
        'enable_api', 'disable_api', 'export_selected'
    ]
    
    fieldsets = (
        ('🔐 Authentification', {
            'fields': ('email', 'username', 'password')
        }),
        ('👤 Informations personnelles', {
            'fields': ('first_name', 'last_name', 'phone', 'avatar')
        }),
        ('💼 Professionnel', {
            'fields': ('department', 'job_title', 'employee_id')
        }),
        ('🎭 Rôle & Statut', {
            'fields': ('role', 'status', 'is_active', 'is_verified')
        }),
        ('🔒 Sécurité', {
            'fields': ('two_factor_enabled', 'failed_login_attempts', 'account_locked_until'),
            'classes': ('collapse',)
        }),
        ('⚙️ API', {
            'fields': ('api_access_enabled', 'api_rate_limit'),
            'classes': ('collapse',)
        }),
        ('🎨 Préférences', {
            'fields': ('timezone', 'language', 'theme'),
            'classes': ('collapse',)
        }),
        ('👥 Groupes & Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('📊 Activité', {
            'fields': ('last_login', 'last_activity_at', 'last_login_ip', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'failed_login_attempts', 'account_locked_until', 'last_login',
        'last_activity_at', 'last_login_ip', 'date_joined'
    ]
    
    filter_horizontal = ['groups', 'user_permissions']
    
    # ========================================================================
    # MÉTHODES D'AFFICHAGE
    # ========================================================================
    
    def role_badge(self, obj):
        """Badge de rôle avec couleur"""
        colors = {
            'superadmin': 'danger',
            'network_admin': 'warning',
            'monitor': 'info',
            'viewer': 'dark',
        }
        color = colors.get(obj.role, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Rôle'
    role_badge.admin_order_field = 'role'
    
    def status_badge(self, obj):
        """Badge de statut"""
        colors = {
            'active': 'success',
            'inactive': 'secondary',
            'suspended': 'danger',
            'locked': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    status_badge.admin_order_field = 'status'
    
    def security_icons(self, obj):
        """Icônes de sécurité"""
        icons = []
        if obj.is_verified:
            icons.append('<span class="badge bg-success" title="Vérifié">✓</span>')
        if obj.two_factor_enabled:
            icons.append('<span class="badge bg-info" title="2FA">🔐</span>')
        if obj.failed_login_attempts > 0:
            icons.append(f'<span class="badge bg-warning" title="{obj.failed_login_attempts} échecs">⚠️</span>')
        
        return format_html(' '.join(icons)) if icons else '-'
    security_icons.short_description = 'Sécurité'
    
    def api_status(self, obj):
        """Statut API"""
        if obj.api_access_enabled:
            return format_html(
                '<span class="badge bg-success">✓ {} req/h</span>',
                obj.api_rate_limit
            )
        return format_html('<span class="badge bg-secondary">✗</span>')
    api_status.short_description = 'API'
    
    def last_activity(self, obj):
        """Dernière activité"""
        if obj.last_activity_at:
            delta = timezone.now() - obj.last_activity_at
            if delta.days > 0:
                return f"{delta.days}j"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600}h"
            elif delta.seconds > 60:
                return f"{delta.seconds // 60}m"
            return "maintenant"
        return '-'
    last_activity.short_description = 'Activité'
    last_activity.admin_order_field = 'last_activity_at'
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    def activate_users(self, request, queryset):
        updated = queryset.update(status='active', is_active=True)
        self.message_user(request, f'✅ {updated} utilisateur(s) activé(s).', messages.SUCCESS)
    activate_users.short_description = "✅ Activer la sélection"
    
    def deactivate_users(self, request, queryset):
        if request.user in queryset:
            self.message_user(request, "❌ Impossible de se désactiver soi-même.", messages.ERROR)
            queryset = queryset.exclude(id=request.user.id)
        updated = queryset.update(status='inactive', is_active=False)
        self.message_user(request, f'⏸️ {updated} utilisateur(s) désactivé(s).', messages.SUCCESS)
    deactivate_users.short_description = "⏸️ Désactiver la sélection"
    
    def suspend_users(self, request, queryset):
        if request.user in queryset:
            self.message_user(request, "❌ Impossible de se suspendre soi-même.", messages.ERROR)
            queryset = queryset.exclude(id=request.user.id)
        lock_until = timezone.now() + timedelta(days=7)
        updated = queryset.update(status='suspended', is_active=False, account_locked_until=lock_until)
        self.message_user(request, f'🚫 {updated} utilisateur(s) suspendu(s) 7 jours.', messages.SUCCESS)
    suspend_users.short_description = "🚫 Suspendre la sélection"
    
    def unlock_users(self, request, queryset):
        updated = queryset.filter(status='locked').update(
            status='active', is_active=True, failed_login_attempts=0, account_locked_until=None
        )
        self.message_user(request, f'🔓 {updated} utilisateur(s) déverrouillé(s).', messages.SUCCESS)
    unlock_users.short_description = "🔓 Déverrouiller"
    
    def enable_api(self, request, queryset):
        updated = queryset.update(api_access_enabled=True)
        self.message_user(request, f'✓ API activée pour {updated} utilisateur(s).', messages.SUCCESS)
    enable_api.short_description = "✓ Activer API"
    
    def disable_api(self, request, queryset):
        updated = queryset.update(api_access_enabled=False)
        self.message_user(request, f'✗ API désactivée pour {updated} utilisateur(s).', messages.SUCCESS)
    disable_api.short_description = "✗ Désactiver API"
    
    def export_selected(self, request, queryset):
        """Export JSON"""
        from django.http import HttpResponse
        data = []
        for user in queryset:
            data.append({
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'status': user.status,
                'department': user.department,
                'created_at': user.created_at.isoformat() if user.created_at else None,
            })
        response = HttpResponse(json.dumps(data, indent=2, ensure_ascii=False), 
                               content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="utilisateurs_olt_export.json"'
        return response
    export_selected.short_description = "📤 Exporter la sélection"
    
    # ========================================================================
    # SÉCURITÉ
    # ========================================================================
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related().prefetch_related(
            'groups', 'user_permissions', 'teams'
        )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            readonly.extend(['role', 'is_superuser', 'is_staff'])
        return readonly
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        UserActivity.objects.create(
            user=request.user,
            action='update' if change else 'create',
            description=f"Utilisateur {obj.email} {'modifié' if change else 'créé'} via admin",
            resource_type='user',
            resource_id=str(obj.id),
            ip_address=request.META.get('REMOTE_ADDR'),
            success=True
        )


# ============================================================================
# ADMIN DES ÉQUIPES
# ============================================================================

@admin.register(Team)
class TeamAdmin(ImportExportModelAdmin):
    """Administration des équipes OLT"""
    
    resource_class = TeamResource
    
    list_display = ['name', 'team_lead_link', 'members_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'team_lead__email']
    filter_horizontal = ['members']
    raw_id_fields = ['team_lead']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('📋 Informations', {
            'fields': ('name', 'description')
        }),
        ('👥 Membres', {
            'fields': ('team_lead', 'members')
        }),
    )
    
    def team_lead_link(self, obj):
        if obj.team_lead:
            url = reverse('admin:users_user_change', args=[obj.team_lead.id])
            return format_html('<a href="{}">{}</a>', url, obj.team_lead.email)
        return '-'
    team_lead_link.short_description = 'Chef'
    
    def members_count(self, obj):
        count = obj.members.count()
        return format_html('<span class="badge bg-primary">{}</span>', count)
    members_count.short_description = 'Membres'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            members_count=models.Count('members')
        )


# ============================================================================
# ADMIN DES RÔLES
# ============================================================================

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Administration des rôles OLT"""
    
    list_display = ['name', 'permissions_badge', 'permissions_preview', 'created_at']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('🎭 Rôle OLT', {
            'fields': ('name', 'description')
        }),
        ('🔑 Permissions', {
            'fields': ('permissions',),
            'description': 'Format JSON: ["permission1", "permission2", ...]'
        }),
    )
    
    def permissions_badge(self, obj):
        count = len(obj.permissions) if obj.permissions else 0
        return format_html('<span class="badge bg-primary">{}</span>', count)
    permissions_badge.short_description = 'Nb'
    
    def permissions_preview(self, obj):
        if not obj.permissions:
            return '-'
        perms = obj.permissions
        if len(perms) > 3:
            return f"{', '.join(perms[:3])} et {len(perms)-3} autre(s)"
        return ', '.join(perms)
    permissions_preview.short_description = 'Aperçu'
    
    def save_model(self, request, obj, form, change):
        if isinstance(obj.permissions, str):
            try:
                obj.permissions = json.loads(obj.permissions)
            except json.JSONDecodeError:
                obj.permissions = [p.strip() for p in obj.permissions.split(',') if p.strip()]
        super().save_model(request, obj, form, change)


# ============================================================================
# ADMIN DES PERMISSIONS
# ============================================================================

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Administration des permissions OLT"""
    
    list_display = ['code', 'name', 'category', 'created_at']
    list_filter = ['category']
    search_fields = ['code', 'name', 'description']
    list_per_page = 50
    
    fieldsets = (
        ('🔑 Permission OLT', {
            'fields': ('code', 'name', 'description', 'category')
        }),
    )


# ============================================================================
# ADMIN DES ACTIVITÉS
# ============================================================================

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Administration des activités (lecture seule)"""
    
    list_display = [
        'created_at', 'user_link', 'action_badge', 
        'severity_badge', 'description_short', 'ip_address'
    ]
    list_filter = ['action', 'severity', 'success', 'created_at']
    search_fields = ['user__email', 'description', 'ip_address']
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    readonly_fields = ['user', 'action', 'severity', 'description', 
                      'resource_type', 'resource_id', 'resource_name',
                      'ip_address', 'user_agent', 'metadata', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Utilisateur'
    
    def action_badge(self, obj):
        colors = {
            'login': 'primary', 'logout': 'secondary', 'create': 'success',
            'update': 'warning', 'delete': 'danger', 'view': 'info',
            'export': 'info', 'import': 'info', 'share': 'success',
            'schedule': 'info', 'olt_add': 'success', 'olt_edit': 'warning',
            'olt_delete': 'danger', 'olt_test': 'info', 'alert_ack': 'warning',
            'alert_resolve': 'success', 'diagnostic_run': 'primary',
        }
        color = colors.get(obj.action, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_action_display())
    action_badge.short_description = 'Action'
    
    def severity_badge(self, obj):
        colors = {'low': 'success', 'medium': 'warning', 'high': 'danger', 'critical': 'danger'}
        color = colors.get(obj.severity, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_severity_display())
    severity_badge.short_description = 'Sévérité'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
