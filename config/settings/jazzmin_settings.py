"""
Jazzmin Admin Settings for OLT Supervision Platform - Core & Users only
"""
JAZZMIN_SETTINGS = {
    # ========================================================================
    # BRANDING
    # ========================================================================
    "site_title": "OLT Supervision Platform",
    "site_header": "OLT Administrator",
    "site_brand": "📡 OLT Supervision",
    "site_logo": None,
    "login_logo": None,
    "site_icon": None,
    "welcome_sign": "🌟 Welcome to OLT Supervision - Network Monitoring Platform",
    "copyright": "OLT Supervision 2026 | v1.0.0",    
    
    # ========================================================================
    # TOP MENU LINKS
    # ========================================================================
    "topmenu_links": [
        {"name": "🏠 Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "👥 Users", "url": "/admin/users/", "new_window": False},
        {"name": "⚙️ Core Config", "url": "/admin/core/", "new_window": False},
        {"name": "📚 API Docs", "url": "/api/schema/swagger-ui/", "new_window": True},
        {"name": "📖 ReDoc", "url": "/api/schema/redoc/", "new_window": True},
        {"name": "📧 Support", "url": "mailto:support@oltsupervision.com", "new_window": True},
    ],
    
    # ========================================================================
    # USER MENU LINKS
    # ========================================================================
    "usermenu_links": [
        {"model": "users.user"},
        {"name": "🔐 My Profile", "url": "/admin/users/user/", "icon": "fas fa-user-circle"},
        {"name": "⚙️ Account Settings", "url": "/admin/account/", "icon": "fas fa-cog"},
        {"name": "📄 Documentation", "url": "https://docs.oltsupervision.com", "new_window": True},
    ],
    
    # ========================================================================
    # SIDEBAR CONFIGURATION
    # ========================================================================
    "show_sidebar": True,
    "navigation_expanded": False,
    "hide_apps": [],
    "hide_models": [],
    
    # ========================================================================
    # ORDER WITH RESPECT TO - Organisation hiérarchique
    # ========================================================================
    "order_with_respect_to": [
        "users",           # Section 1: Gestion des utilisateurs
        "core",            # Section 2: Configuration Core
        "auth",            # Section 3: Authentification
        "authtoken",       
        "token_blacklist",
        "django_celery_beat",
        "django_celery_results",
    ],
    
    # ========================================================================
    # ICONS - Tous les modèles
    # ========================================================================
    "icons": {
        # SECTION 1: GESTION DES UTILISATEURS
        "users": "fas fa-users-cog",
        "users.User": "fas fa-user-circle",
        "users.Team": "fas fa-users",
        "users.Role": "fas fa-user-tag",
        "users.Permission": "fas fa-key",
        "users.UserActivity": "fas fa-history",
        
        # SECTION 2: CORE
        "core": "fas fa-cogs",
        "core.Config": "fas fa-sliders-h",
        
        # SECTION 3: AUTHENTIFICATION
        "auth": "fas fa-lock",
        "auth.Group": "fas fa-users-cog",
        "auth.Permission": "fas fa-key",
        
        # SECTION 4: TOKENS
        "authtoken": "fas fa-key",
        "authtoken.Token": "fas fa-token",
        "authtoken.tokenproxy": "fas fa-key",
        
        # SECTION 5: TOKEN BLACKLIST
        "token_blacklist": "fas fa-ban",
        "token_blacklist.BlacklistedToken": "fas fa-ban",
        "token_blacklist.OutstandingToken": "fas fa-clock",
        
        # SECTION 6: CELERY BEAT
        "django_celery_beat": "fas fa-clock",
        "django_celery_beat.ClockedSchedule": "fas fa-clock",
        "django_celery_beat.CrontabSchedule": "fas fa-calendar-alt",
        "django_celery_beat.IntervalSchedule": "fas fa-hourglass",
        "django_celery_beat.PeriodicTask": "fas fa-tasks",
        "django_celery_beat.PeriodicTasks": "fas fa-list",
        "django_celery_beat.SolarSchedule": "fas fa-sun",
        
        # SECTION 7: CELERY RESULTS
        "django_celery_results": "fas fa-chart-line",
        "django_celery_results.TaskResult": "fas fa-check-circle",
        "django_celery_results.GroupResult": "fas fa-layer-group",
        "django_celery_results.ChordCounter": "fas fa-code-branch",
    },
    
    # ========================================================================
    # DEFAULT ICONS
    # ========================================================================
    "default_icon_parents": "fas fa-folder-open",
    "default_icon_children": "fas fa-file",
    
    # ========================================================================
    # CUSTOM LINKS - Liens rapides
    # ========================================================================
    "custom_links": {
        "users": [
            {"name": "➕ Créer utilisateur", "url": "/admin/users/user/add/", "icon": "fas fa-user-plus", "permissions": ["users.add_user"]},
            {"name": "👥 Nouvelle équipe", "url": "/admin/users/team/add/", "icon": "fas fa-users", "permissions": ["users.add_team"]},
            {"name": "🎭 Nouveau rôle", "url": "/admin/users/role/add/", "icon": "fas fa-user-tag", "permissions": ["users.add_role"]},
            {"name": "🔑 Nouvelle permission", "url": "/admin/users/permission/add/", "icon": "fas fa-key", "permissions": ["users.add_permission"]},
            {"name": "📊 Voir activités", "url": "/admin/users/useractivity/", "icon": "fas fa-history", "permissions": ["users.view_useractivity"]},
        ],
        "core": [
            {"name": "⚙️ Nouvelle configuration", "url": "/admin/core/config/add/", "icon": "fas fa-plus-circle", "permissions": ["core.add_config"]},
            {"name": "📋 Voir configurations", "url": "/admin/core/config/", "icon": "fas fa-list", "permissions": ["core.view_config"]},
        ],
    },
    
    # ========================================================================
    # RELATED MODAL
    # ========================================================================
    "related_modal_active": True,
    
    # ========================================================================
    # CUSTOM CSS/JS
    # ========================================================================
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    
    # ========================================================================
    # CHANGE FORM FORMAT
    # ========================================================================
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        # Users
        "users.user": "vertical_tabs",
        "users.team": "horizontal_tabs",
        "users.role": "collapsible",
        "users.permission": "collapsible",
        "users.useractivity": "collapsible",
        
        # Core
        "core.config": "horizontal_tabs",
        
        # Celery
        "django_celery_beat.periodictask": "horizontal_tabs",
        "django_celery_beat.crontabschedule": "collapsible",
        "django_celery_beat.intervalschedule": "collapsible",
        
        # Token Blacklist
        "token_blacklist.blacklistedtoken": "collapsible",
        "token_blacklist.outstandingtoken": "collapsible",
    },
    
    # ========================================================================
    # LANGUAGE - Désactivé
    # ========================================================================
    "language_chooser": False,
}

# ========================================================================
# JAZZMIN UI TWEAKS
# ========================================================================
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "navbar_small_text": False,
    "navbar_fixed": True,
    "navbar": "navbar-light bg-white",
    "navbar_class": "shadow-sm border-bottom",
    "sidebar": "sidebar-light-primary",
    "sidebar_fixed": True,
    "sidebar_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "footer_fixed": False,
    "footer_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-light",
    "brand_colour_bg": "bg-white",
    "body_small_text": False,
    "no_navbar_border": False,
    "layout_boxed": False,
    "accent": "accent-primary",
    "button_classes": {
        "primary": "btn-primary btn-sm",
        "secondary": "btn-secondary btn-sm",
        "info": "btn-info btn-sm",
        "warning": "btn-warning btn-sm",
        "danger": "btn-danger btn-sm",
        "success": "btn-success btn-sm",
        "outline-primary": "btn-outline-primary btn-sm",
    },
    "actions_sticky_top": True,
}

# ========================================================================
# CUSTOM DASHBOARD - Tableau de bord personnalisé (Core & Users)
# ========================================================================
JAZZMIN_DASHBOARD = {
    "welcome_message": """
        <div class="alert alert-primary alert-dismissible fade show" role="alert">
            <strong>👋 Welcome back, {user}!</strong>
            <span class="badge bg-success ms-2">{active_users}/{total_users} users active</span>
            <span class="badge bg-info ms-2">{total_teams} teams</span>
            <span class="badge bg-secondary ms-2">{total_roles} roles</span>
            <span class="badge bg-warning ms-2">{activities_24h} activities</span>
            <span class="badge bg-primary ms-2">{total_configs} configs</span>
            <span class="badge bg-purple ms-2">{api_users} API users</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    """,
    
    "quick_actions": [
        # Users
        {"name": "➕ Create User", "url": "/admin/users/user/add/", "icon": "fas fa-user-plus", "color": "success"},
        {"name": "👥 New Team", "url": "/admin/users/team/add/", "icon": "fas fa-users", "color": "primary"},
        {"name": "🎭 New Role", "url": "/admin/users/role/add/", "icon": "fas fa-user-tag", "color": "info"},
        {"name": "🔑 New Permission", "url": "/admin/users/permission/add/", "icon": "fas fa-key", "color": "warning"},
        
        # Core
        {"name": "⚙️ New Config", "url": "/admin/core/config/add/", "icon": "fas fa-sliders-h", "color": "secondary"},
        {"name": "📋 View Configs", "url": "/admin/core/config/", "icon": "fas fa-list", "color": "dark"},
    ],
    
    "stats_cards": [
        # Users stats
        {"title": "Total Users", "value": "{total_users}", "icon": "fas fa-users", "color": "primary"},
        {"title": "Active Users", "value": "{active_users}", "icon": "fas fa-user-check", "color": "success"},
        {"title": "Total Teams", "value": "{total_teams}", "icon": "fas fa-users-cog", "color": "info"},
        {"title": "Total Roles", "value": "{total_roles}", "icon": "fas fa-user-tag", "color": "warning"},
        {"title": "Permissions", "value": "{total_permissions}", "icon": "fas fa-key", "color": "danger"},
        
        # API & Security
        {"title": "API Users", "value": "{api_users}", "icon": "fas fa-plug", "color": "info"},
        {"title": "2FA Enabled", "value": "{two_factor_enabled}", "icon": "fas fa-mobile-alt", "color": "success"},
        {"title": "Verified Users", "value": "{verified_users}", "icon": "fas fa-check-circle", "color": "primary"},
        
        # Activities
        {"title": "Activities (24h)", "value": "{activities_24h}", "icon": "fas fa-history", "color": "secondary"},
        {"title": "Failed Logins (24h)", "value": "{failed_logins}", "icon": "fas fa-exclamation-triangle", "color": "danger"},
        
        # Core Configs
        {"title": "Configurations", "value": "{total_configs}", "icon": "fas fa-cogs", "color": "warning"},
        {"title": "Encrypted Configs", "value": "{encrypted_configs}", "icon": "fas fa-lock", "color": "danger"},
    ],
    
    "recent_activities": {
        "title": "📋 Recent Activities",
        "limit": 10,
        "model": "users.UserActivity",
        "fields": ["user", "action", "severity", "created_at"],
    },
    
    "recent_users": {
        "title": "👤 Recently Added Users",
        "limit": 5,
        "model": "users.User",
        "fields": ["email", "role", "status", "created_at"],
        "order_by": ["-created_at"],
    },
    
    "recent_teams": {
        "title": "👥 Recent Teams",
        "limit": 5,
        "model": "users.Team",
        "fields": ["name", "team_lead", "created_at"],
        "order_by": ["-created_at"],
    },
    
    "recent_configs": {
        "title": "⚙️ Recent Configurations",
        "limit": 5,
        "model": "core.Config",
        "fields": ["key", "config_type", "created_at"],
        "order_by": ["-created_at"],
    },
    
    "charts": {
        "users_by_role": {
            "title": "User Distribution by Role",
            "type": "pie",
            "data_url": "/api/users/users/stats/",
        },
        "users_by_status": {
            "title": "User Status Distribution",
            "type": "pie",
            "data_url": "/api/users/users/stats/",
        },
        "activities_by_action": {
            "title": "Activities by Action (Last 7 Days)",
            "type": "bar",
            "data_url": "/api/users/activities/stats/",
        },
        "activities_by_severity": {
            "title": "Activities by Severity",
            "type": "pie",
            "data_url": "/api/users/activities/stats/",
        },
        "configs_by_type": {
            "title": "Configurations by Type",
            "type": "pie",
            "data_url": "/api/core/config/stats/",
        },
    },
}

# ========================================================================
# FONCTIONS UTILITAIRES POUR LE DASHBOARD (Core & Users)
# ========================================================================

def get_dashboard_stats():
    """
    Fonction pour récupérer les statistiques du dashboard (Core & Users)
    """
    from django.contrib.auth import get_user_model
    from apps.users.models import UserActivity, Team, Role, Permission
    from apps.core.models import Config
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count
    
    User = get_user_model()
    
    # ========================================================================
    # STATISTIQUES USERS
    # ========================================================================
    total_users = User.objects.count()
    active_users = User.objects.filter(status='active', is_active=True).count()
    total_teams = Team.objects.count()
    total_roles = Role.objects.count()
    total_permissions = Permission.objects.count()
    
    # Statistiques API & Sécurité
    api_users = User.objects.filter(api_access_enabled=True).count()
    two_factor_enabled = User.objects.filter(two_factor_enabled=True).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Activités
    last_24h = timezone.now() - timedelta(hours=24)
    activities_24h = UserActivity.objects.filter(created_at__gte=last_24h).count()
    failed_logins = UserActivity.objects.filter(
        action='login',
        success=False,
        created_at__gte=last_24h
    ).count()
    
    # ========================================================================
    # STATISTIQUES CORE
    # ========================================================================
    total_configs = Config.objects.count()
    encrypted_configs = Config.objects.filter(is_encrypted=True).count()
    
    config_by_type = {}
    for config_type, _ in Config.CONFIG_TYPES:
        count = Config.objects.filter(config_type=config_type).count()
        if count > 0:
            config_by_type[config_type] = count
    
    return {
        # Users
        'total_users': total_users,
        'active_users': active_users,
        'total_teams': total_teams,
        'total_roles': total_roles,
        'total_permissions': total_permissions,
        'api_users': api_users,
        'two_factor_enabled': two_factor_enabled,
        'verified_users': verified_users,
        'activities_24h': activities_24h,
        'failed_logins': failed_logins,
        
        # Core
        'total_configs': total_configs,
        'encrypted_configs': encrypted_configs,
        'config_by_type': config_by_type,
    }