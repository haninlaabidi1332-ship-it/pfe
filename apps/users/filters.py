# apps/users/filters.py
"""
Users App Filters - Filtres personnalisés pour OLT Supervision
"""
import django_filters
from django_filters import rest_framework as filters
from django.db import models
from django.db.models import Q, Count
from .models import User, Team, Role, Permission, UserActivity


class UserFilter(filters.FilterSet):
    """Filtres avancés pour les utilisateurs OLT Supervision"""
    
    # Filtres texte
    username = filters.CharFilter(lookup_expr='icontains', label="Nom d'utilisateur")
    email = filters.CharFilter(lookup_expr='icontains', label="Email")
    first_name = filters.CharFilter(lookup_expr='icontains', label="Prénom")
    last_name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    department = filters.CharFilter(lookup_expr='icontains', label="Département")
    job_title = filters.CharFilter(lookup_expr='icontains', label="Poste")
    employee_id = filters.CharFilter(lookup_expr='icontains', label="Matricule")
    phone = filters.CharFilter(lookup_expr='icontains', label="Téléphone")
    
    # Filtres choix (rôles OLT)
    role = filters.ChoiceFilter(choices=User.ROLE_CHOICES, label="Rôle")
    status = filters.ChoiceFilter(choices=User.STATUS_CHOICES, label="Statut")
    
    # Filtres booléens
    is_active = filters.BooleanFilter(label="Actif")
    is_verified = filters.BooleanFilter(label="Vérifié")
    two_factor_enabled = filters.BooleanFilter(label="2FA activé")
    api_access_enabled = filters.BooleanFilter(label="Accès API")
    
    # Filtres de dates
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', 
                                          label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', 
                                           label="Créé avant")
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte', 
                                          label="Mis à jour après")
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte', 
                                           label="Mis à jour avant")
    last_login_after = filters.DateTimeFilter(field_name='last_login', lookup_expr='gte', 
                                             label="Dernière connexion après")
    last_login_before = filters.DateTimeFilter(field_name='last_login', lookup_expr='lte', 
                                              label="Dernière connexion avant")
    last_activity_after = filters.DateTimeFilter(field_name='last_activity_at', lookup_expr='gte', 
                                                label="Dernière activité après")
    last_activity_before = filters.DateTimeFilter(field_name='last_activity_at', lookup_expr='lte', 
                                                 label="Dernière activité avant")
    date_joined_after = filters.DateTimeFilter(field_name='date_joined', lookup_expr='gte', 
                                              label="Inscrit après")
    date_joined_before = filters.DateTimeFilter(field_name='date_joined', lookup_expr='lte', 
                                               label="Inscrit avant")
    
    # Filtres de relations
    team = filters.UUIDFilter(field_name='teams__id', label="ID équipe")
    team_name = filters.CharFilter(field_name='teams__name', lookup_expr='icontains', 
                                   label="Nom d'équipe")
    led_team = filters.UUIDFilter(field_name='led_teams__id', label="ID équipe dirigée")
    
    # Filtres OLT spécifiques
    is_network_admin = filters.BooleanFilter(method='filter_network_admin', label="Est admin réseau")
    is_monitor = filters.BooleanFilter(method='filter_monitor', label="Est superviseur")
    can_manage_olts = filters.BooleanFilter(method='filter_can_manage_olts', label="Peut gérer les OLT")
    
    # Filtres personnalisés
    search = filters.CharFilter(method='filter_search', label="Recherche")
    is_admin = filters.BooleanFilter(method='filter_is_admin', label="Est administrateur")
    has_teams = filters.BooleanFilter(method='filter_has_teams', label="A des équipes")
    has_activity = filters.BooleanFilter(method='filter_has_activity', label="A des activités")
    min_activities = filters.NumberFilter(method='filter_min_activities', 
                                          label="Minimum d'activités")
    max_activities = filters.NumberFilter(method='filter_max_activities', 
                                          label="Maximum d'activités")
    
    class Meta:
        model = User
        fields = [
            'role', 'status', 'is_active', 'is_verified', 
            'two_factor_enabled', 'api_access_enabled'
        ]
    
    def filter_search(self, queryset, name, value):
        """Recherche multi-champs"""
        return queryset.filter(
            Q(username__icontains=value) |
            Q(email__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(department__icontains=value) |
            Q(employee_id__icontains=value)
        )
    
    def filter_is_admin(self, queryset, name, value):
        """Filtre les administrateurs (superadmin ou network_admin)"""
        admin_roles = ['superadmin', 'network_admin']
        if value:
            return queryset.filter(role__in=admin_roles)
        return queryset.exclude(role__in=admin_roles)
    
    def filter_network_admin(self, queryset, name, value):
        """Filtre les administrateurs réseau"""
        if value:
            return queryset.filter(role='network_admin')
        return queryset.exclude(role='network_admin')
    
    def filter_monitor(self, queryset, name, value):
        """Filtre les superviseurs"""
        if value:
            return queryset.filter(role='monitor')
        return queryset.exclude(role='monitor')
    
    def filter_can_manage_olts(self, queryset, name, value):
        """Filtre les utilisateurs qui peuvent gérer les OLT"""
        manager_roles = ['superadmin', 'network_admin']
        if value:
            return queryset.filter(role__in=manager_roles)
        return queryset.exclude(role__in=manager_roles)
    
    def filter_has_teams(self, queryset, name, value):
        """Filtre les utilisateurs avec/sans équipes"""
        if value:
            return queryset.filter(teams__isnull=False).distinct()
        return queryset.filter(teams__isnull=True).distinct()
    
    def filter_has_activity(self, queryset, name, value):
        """Filtre les utilisateurs avec/sans activité"""
        if value:
            return queryset.filter(activities__isnull=False).distinct()
        return queryset.filter(activities__isnull=True).distinct()
    
    def filter_min_activities(self, queryset, name, value):
        """Filtre les utilisateurs avec un minimum d'activités"""
        return queryset.annotate(
            activity_count=Count('activities')
        ).filter(activity_count__gte=value)
    
    def filter_max_activities(self, queryset, name, value):
        """Filtre les utilisateurs avec un maximum d'activités"""
        return queryset.annotate(
            activity_count=Count('activities')
        ).filter(activity_count__lte=value)


class TeamFilter(filters.FilterSet):
    """Filtres pour les équipes OLT"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    
    # Filtres de relations
    team_lead = filters.UUIDFilter(field_name='team_lead__id', label="ID chef d'équipe")
    team_lead_name = filters.CharFilter(
        field_name='team_lead__email', 
        lookup_expr='icontains',
        label="Email du chef"
    )
    member = filters.UUIDFilter(field_name='members__id', label="ID membre")
    member_name = filters.CharFilter(
        field_name='members__email', 
        lookup_expr='icontains',
        label="Email du membre"
    )
    
    # Filtres de dates
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', 
                                          label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', 
                                           label="Créé avant")
    
    # Filtres personnalisés
    min_members = filters.NumberFilter(method='filter_min_members', 
                                       label="Minimum de membres")
    max_members = filters.NumberFilter(method='filter_max_members', 
                                       label="Maximum de membres")
    has_team_lead = filters.BooleanFilter(method='filter_has_team_lead', 
                                         label="A un chef")
    
    class Meta:
        model = Team
        fields = ['name', 'team_lead']
    
    def filter_min_members(self, queryset, name, value):
        """Filtre les équipes avec un minimum de membres"""
        return queryset.annotate(
            members_count=Count('members')
        ).filter(members_count__gte=value)
    
    def filter_max_members(self, queryset, name, value):
        """Filtre les équipes avec un maximum de membres"""
        return queryset.annotate(
            members_count=Count('members')
        ).filter(members_count__lte=value)
    
    def filter_has_team_lead(self, queryset, name, value):
        """Filtre les équipes avec/sans chef"""
        if value:
            return queryset.filter(team_lead__isnull=False)
        return queryset.filter(team_lead__isnull=True)


class RoleFilter(filters.FilterSet):
    """Filtres pour les rôles OLT"""
    
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    
    # Filtres de dates
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', 
                                          label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', 
                                           label="Créé avant")
    
    # Filtres personnalisés
    has_permission = filters.CharFilter(method='filter_has_permission', 
                                        label="A la permission")
    min_permissions = filters.NumberFilter(method='filter_min_permissions', 
                                          label="Minimum de permissions")
    max_permissions = filters.NumberFilter(method='filter_max_permissions', 
                                          label="Maximum de permissions")
    
    class Meta:
        model = Role
        fields = ['name']
    
    def filter_has_permission(self, queryset, name, value):
        """Filtre les rôles qui ont une permission spécifique"""
        return queryset.filter(permissions__contains=[value])
    
    def filter_min_permissions(self, queryset, name, value):
        """Filtre les rôles avec un minimum de permissions"""
        result_ids = []
        for role in queryset:
            if len(role.permissions) >= value:
                result_ids.append(role.id)
        return queryset.filter(id__in=result_ids)
    
    def filter_max_permissions(self, queryset, name, value):
        """Filtre les rôles avec un maximum de permissions"""
        result_ids = []
        for role in queryset:
            if len(role.permissions) <= value:
                result_ids.append(role.id)
        return queryset.filter(id__in=result_ids)


class PermissionFilter(filters.FilterSet):
    """Filtres pour les permissions OLT"""
    
    code = filters.CharFilter(lookup_expr='icontains', label="Code")
    name = filters.CharFilter(lookup_expr='icontains', label="Nom")
    description = filters.CharFilter(lookup_expr='icontains', label="Description")
    category = filters.ChoiceFilter(choices=Permission.CATEGORY_CHOICES, label="Catégorie")
    
    # Filtres de dates
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', 
                                          label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', 
                                           label="Créé avant")
    
    class Meta:
        model = Permission
        fields = ['code', 'category']


class UserActivityFilter(filters.FilterSet):
    """Filtres pour les activités utilisateur OLT"""
    
    user = filters.UUIDFilter(field_name='user__id', label="ID utilisateur")
    user_email = filters.CharFilter(field_name='user__email', lookup_expr='icontains', 
                                    label="Email utilisateur")
    action = filters.ChoiceFilter(choices=UserActivity.ACTION_CHOICES, label="Action")
    severity = filters.ChoiceFilter(choices=UserActivity.SEVERITY_CHOICES, label="Sévérité")
    success = filters.BooleanFilter(label="Succès")
    
    resource_type = filters.CharFilter(lookup_expr='icontains', label="Type de ressource")
    resource_id = filters.CharFilter(lookup_expr='icontains', label="ID ressource")
    resource_name = filters.CharFilter(lookup_expr='icontains', label="Nom ressource")
    ip_address = filters.CharFilter(lookup_expr='icontains', label="Adresse IP")
    
    # Filtres de dates
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', 
                                          label="Créé après")
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', 
                                           label="Créé avant")
    
    # Filtres personnalisés
    search = filters.CharFilter(method='filter_search', label="Recherche")
    date = filters.DateFilter(method='filter_date', label="Date exacte")
    week = filters.NumberFilter(method='filter_week', label="Semaine")
    month = filters.NumberFilter(method='filter_month', label="Mois")
    
    class Meta:
        model = UserActivity
        fields = ['user', 'action', 'severity', 'success', 'resource_type']
    
    def filter_search(self, queryset, name, value):
        """Recherche dans la description"""
        return queryset.filter(description__icontains=value)
    
    def filter_date(self, queryset, name, value):
        """Filtre par date exacte"""
        return queryset.filter(created_at__date=value)
    
    def filter_week(self, queryset, name, value):
        """Filtre par semaine (numéro de semaine)"""
        from django.db.models.functions import ExtractWeek
        return queryset.annotate(week=ExtractWeek('created_at')).filter(week=value)
    
    def filter_month(self, queryset, name, value):
        """Filtre par mois"""
        return queryset.filter(created_at__month=value)


class UserStatsFilter(filters.FilterSet):
    """Filtres pour les statistiques utilisateur OLT"""
    
    date_from = filters.DateFilter(method='filter_date_from', label="Date début")
    date_to = filters.DateFilter(method='filter_date_to', label="Date fin")
    role = filters.ChoiceFilter(choices=User.ROLE_CHOICES, label="Rôle")
    department = filters.CharFilter(lookup_expr='icontains', label="Département")
    
    class Meta:
        model = User
        fields = ['role', 'department']
    
    def filter_date_from(self, queryset, name, value):
        """Filtre les utilisateurs créés après une date"""
        return queryset.filter(created_at__date__gte=value)
    
    def filter_date_to(self, queryset, name, value):
        """Filtre les utilisateurs créés avant une date"""
        return queryset.filter(created_at__date__lte=value)