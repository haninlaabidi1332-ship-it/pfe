# apps/core/permissions.py
"""
Custom Permission Classes for OLT Supervision Platform
"""
from rest_framework import permissions


# ========================================================================
# PERMISSIONS DE BASE (inchangées)
# ========================================================================

class IsSuperAdmin(permissions.BasePermission):
    """Only superadmins can access"""
    message = "👑 Seuls les super-administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'is_superadmin', False))


class IsAdmin(permissions.BasePermission):
    """Superadmins and admins can access"""
    message = "⚙️ Seuls les administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'is_admin', False))


class IsAdminOrReadOnly(permissions.BasePermission):
    """Admins can edit, others can only read"""
    message = "✏️ Vous n'avez pas les droits de modification."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return getattr(request.user, 'is_admin', False)


class IsOwnerOrAdmin(permissions.BasePermission):
    """User is owner of object or admin"""
    message = "🔒 Vous n'êtes pas le propriétaire de cette ressource."
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if getattr(request.user, 'is_admin', False):
            return True
        
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


# ========================================================================
# PERMISSIONS COMBINÉES (inchangées)
# ========================================================================

class IsActiveUser(permissions.BasePermission):
    """User account must be active"""
    message = "⏸️ Votre compte n'est pas actif."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.status == 'active')


class HasAPIAccess(permissions.BasePermission):
    """User has API access enabled"""
    message = "🔑 Votre accès API est désactivé."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.api_access_enabled)


class IsVerified(permissions.BasePermission):
    """User account must be verified"""
    message = "✅ Votre compte doit être vérifié d'abord."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.is_verified)


class IsAdminAndActive(permissions.BasePermission):
    """Must be admin and have active account"""
    message = "⚙️ Vous devez être administrateur avec un compte actif."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'is_admin', False) and 
                request.user.status == 'active')


class HasPermissionCode(permissions.BasePermission):
    """Check if user has specific permission code"""
    required_permission = None
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superadmins have all permissions
        if getattr(request.user, 'is_superadmin', False):
            return True
        
        # Check user's role permissions
        from apps.users.models import Role
        try:
            user_role = Role.objects.get(name=request.user.role)
            permission_code = self.required_permission or getattr(view, 'required_permission', None)
            return user_role.has_permission(permission_code) if permission_code else False
        except Role.DoesNotExist:
            return False


# ========================================================================
# PERMISSIONS SPÉCIFIQUES À LA SUPERVISION OLT
# ========================================================================

class CanManageOLTs(permissions.BasePermission):
    """Permission to manage OLTs (create, update, delete)"""
    message = "📡 Vous n'avez pas la permission de gérer les équipements OLT."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_manage_olts', False))


class CanViewOLTs(permissions.BasePermission):
    """Permission to view OLTs"""
    message = "👀 Vous n'avez pas la permission de voir les équipements OLT."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_view_olts', True))


class CanMonitorOLTs(permissions.BasePermission):
    """Permission to access monitoring features (metrics, BFD, etc.)"""
    message = "📊 Vous n'avez pas la permission d'accéder aux métriques de supervision."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_monitor_olts', False))


class CanManageAlerts(permissions.BasePermission):
    """Permission to manage alerts (acknowledge, resolve, configure)"""
    message = "⚠️ Vous n'avez pas la permission de gérer les alertes."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_manage_alerts', False))


class CanViewAlerts(permissions.BasePermission):
    """Permission to view alerts"""
    message = "👀 Vous n'avez pas la permission de voir les alertes."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_view_alerts', True))


class CanRunDiagnostics(permissions.BasePermission):
    """Permission to run diagnostic commands on OLTs"""
    message = "🔧 Vous n'avez pas la permission d'exécuter des diagnostics."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_run_diagnostics', False))


class CanConfigureSNMP(permissions.BasePermission):
    """Permission to modify SNMP settings"""
    message = "📡 Vous n'avez pas la permission de modifier la configuration SNMP."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_configure_snmp', False))


class CanViewAnalytics(permissions.BasePermission):
    """Permission to view ML analytics and predictions"""
    message = "🤖 Vous n'avez pas la permission d'accéder aux analyses prédictives."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'can_view_analytics', False))


# ========================================================================
# PERMISSIONS COMBINÉES POUR LA SUPERVISION
# ========================================================================

class IsNetworkAdmin(permissions.BasePermission):
    """User is a network administrator (full OLT management + monitoring)"""
    message = "🌐 Seuls les administrateurs réseau peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                (getattr(request.user, 'is_admin', False) or 
                 getattr(request.user, 'is_network_admin', False)))


class IsReadOnlyMonitor(permissions.BasePermission):
    """User has read-only access to monitoring data"""
    message = "📉 Vous avez un accès en lecture seule à la supervision."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return getattr(request.user, 'is_admin', False) or getattr(request.user, 'can_manage_alerts', False)


class HasFullMonitoringAccess(permissions.BasePermission):
    """User has full access to all monitoring features"""
    message = "🔒 Accès complet à la supervision requis."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                (getattr(request.user, 'is_superadmin', False) or
                 getattr(request.user, 'is_admin', False) or
                 getattr(request.user, 'is_network_admin', False)))