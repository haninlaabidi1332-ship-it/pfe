# apps/users/views.py
"""
Users Views - Gestion des utilisateurs pour OLT Supervision Platform
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.core.permissions import (
    IsSuperAdmin, IsAdmin, IsAdminOrReadOnly,
    IsActiveUser, HasAPIAccess
)
from apps.core.responses import (
    success_response, created_response, error_response,
    not_found_response, forbidden_response
)
from apps.core.pagination import StandardPagination
from apps.core.utils import get_client_ip, Timer

from .models import User, Team, Role, Permission, UserActivity
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    UserUpdateSerializer, UserMinimalSerializer, UserStatsSerializer,
    TeamSerializer, RoleSerializer, PermissionSerializer,
    UserActivitySerializer, ChangePasswordSerializer
)
from .filters import (
    UserFilter, TeamFilter, RoleFilter, 
    PermissionFilter, UserActivityFilter
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs OLT Supervision
    """
    
    queryset = User.objects.all().select_related().prefetch_related(
        'teams', 'activities'
    )
    serializer_class = UserDetailSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering_fields = ['created_at', 'last_login', 'username', 'email']
    ordering = ['-created_at']
    pagination_class = StandardPagination
    
    def get_serializer_class(self):
        """
        Retourne le sérialiseur approprié selon l'action
        """
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'me':
            return UserDetailSerializer
        elif self.action == 'minimal_list':
            return UserMinimalSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def get_permissions(self):
        """
        Définit les permissions selon l'action
        """
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action == 'list':
            # Pour la liste, seule l'authentification est requise
            permission_classes = [IsAuthenticated]
        elif self.action in ['destroy', 'bulk_delete']:
            permission_classes = [IsAuthenticated, IsSuperAdmin]
        elif self.action in ['update', 'partial_update', 'reset_password', 
                            'toggle_status', 'toggle_api_access']:
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action == 'check_permissions':
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action == 'minimal_list':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsActiveUser, HasAPIAccess]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filtre le queryset selon les permissions de l'utilisateur
        """
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return User.objects.none()
        
        queryset = super().get_queryset()
        
        # SuperAdmin voit tout
        if user.is_superadmin:
            return queryset
        
        # Admin voit tous les utilisateurs
        if user.is_admin:
            return queryset
        
        # Les autres ne voient qu'eux-mêmes
        return queryset.filter(id=user.id)
    
    def list(self, request, *args, **kwargs):
        """
        Liste paginée des utilisateurs
        """
        timer = Timer().start()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        timer.stop()
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            serializer.data, 
            "Utilisateurs récupérés avec succès",
            meta={"query_time_ms": timer.duration_ms()}
        )
    
    def create(self, request, *args, **kwargs):
        """
        Crée un nouvel utilisateur
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=user,
            action='create',
            description=f"Utilisateur {user.email} créé",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return created_response(
            UserDetailSerializer(user).data,
            "Utilisateur créé avec succès"
        )
    
    def update(self, request, *args, **kwargs):
        """
        Met à jour un utilisateur
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description=f"Utilisateur {user.email} mis à jour",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(
            UserDetailSerializer(user).data,
            "Utilisateur mis à jour avec succès"
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Supprime un utilisateur
        """
        instance = self.get_object()
        
        # Empêcher l'auto-suppression
        if instance.id == request.user.id:
            return error_response(
                "Vous ne pouvez pas supprimer votre propre compte",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Journal avant suppression
        user_email = instance.email
        user_id = str(instance.id)
        
        instance.delete()
        
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=request.user,
            action='delete',
            severity='medium',
            description=f"Utilisateur {user_email} supprimé",
            resource_type='user',
            resource_id=user_id,
            resource_name=instance.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(None, "Utilisateur supprimé avec succès")
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Récupère le profil de l'utilisateur connecté
        """
        serializer = UserDetailSerializer(request.user)
        
        # Ajout des informations de session
        data = serializer.data
        data['session'] = {
            'last_activity': timezone.now(),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        return success_response(data, "Profil utilisateur récupéré")
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change le mot de passe de l'utilisateur connecté
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=user,
            action='update',
            severity='medium',
            description="Mot de passe modifié",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(None, "Mot de passe modifié avec succès")
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def reset_password(self, request, pk=None):
        """
        Admin : Réinitialise le mot de passe d'un utilisateur
        """
        user = self.get_object()
        
        # TODO: Envoyer un email de réinitialisation
        # send_password_reset_email(user)
        
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=request.user,
            action='update',
            severity='medium',
            description=f"Réinitialisation du mot de passe pour {user.email}",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(None, f"Email de réinitialisation envoyé à {user.email}")
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def toggle_status(self, request, pk=None):
        """
        Admin : Active/désactive un utilisateur
        """
        user = self.get_object()
        
        # Empêcher l'auto-désactivation
        if user.id == request.user.id:
            return error_response(
                "Vous ne pouvez pas modifier votre propre statut",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        new_status = request.data.get('status')
        if new_status not in ['active', 'inactive', 'suspended']:
            return error_response(
                "Statut invalide. Choisir parmi : active, inactive, suspended",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = user.status
        user.status = new_status
        user.is_active = new_status == 'active'
        user.save()
        
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=request.user,
            action='update',
            severity='medium' if new_status == 'suspended' else 'low',
            description=f"Statut utilisateur changé de {old_status} à {new_status}",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(
            UserDetailSerializer(user).data,
            f"Statut utilisateur mis à jour : {new_status}"
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def toggle_api_access(self, request, pk=None):
        """
        Admin : Active/désactive l'accès API
        """
        user = self.get_object()
        
        user.api_access_enabled = not user.api_access_enabled
        user.save()
        
        status = "activé" if user.api_access_enabled else "désactivé"
        
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=request.user,
            action='update',
            severity='low',
            description=f"Accès API {status} pour {user.email}",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(
            {'api_access_enabled': user.api_access_enabled},
            f"Accès API {status}"
        )
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """
        Récupère les activités d'un utilisateur
        """
        user = self.get_object()
        
        # Vérification des permissions
        if not request.user.is_admin and request.user.id != user.id:
            return forbidden_response(
                "Vous n'avez pas la permission de voir ces activités",
                required_permission="is_admin"
            )
        
        activities = user.activities.all()
        
        # Filtre par nombre de jours
        days = request.query_params.get('days')
        if days:
            try:
                days = int(days)
                cutoff = timezone.now() - timedelta(days=days)
                activities = activities.filter(created_at__gte=cutoff)
            except ValueError:
                pass
        
        page = self.paginate_queryset(activities)
        if page is not None:
            serializer = UserActivitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserActivitySerializer(activities, many=True)
        return success_response(serializer.data, "Activités récupérées")
    
    @action(detail=False, methods=['get'])
    def minimal_list(self, request):
        """
        Liste minimale des utilisateurs (pour les selects)
        """
        users = self.get_queryset()[:50]
        serializer = UserMinimalSerializer(users, many=True)
        return success_response(serializer.data, "Liste minimale des utilisateurs")
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Statistiques globales des utilisateurs
        """
        if not request.user.is_admin:
            return forbidden_response(
                "Accès administrateur requis",
                required_permission="is_admin"
            )
        
        queryset = self.get_queryset()
        
        # Statistiques de base
        total_users = queryset.count()
        active_users = queryset.filter(status='active', is_active=True).count()
        inactive_users = queryset.filter(status='inactive').count()
        
        # Statistiques par rôle
        by_role = {}
        for role, _ in User.ROLE_CHOICES:
            count = queryset.filter(role=role).count()
            if count > 0:
                by_role[role] = count
        
        # Statistiques OLT spécifiques
        network_admins = queryset.filter(role='network_admin').count()
        monitors = queryset.filter(role='monitor').count()
        alert_managers = queryset.filter(
            Q(role__in=['superadmin', 'network_admin'])
        ).count()
        
        # Activités récentes
        last_24h = timezone.now() - timedelta(hours=24)
        recent_activities = UserActivity.objects.filter(
            created_at__gte=last_24h
        ).count()
        
        # Utilisateurs API
        api_users = queryset.filter(api_access_enabled=True).count()
        
        stats_data = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'by_role': by_role,
            'network_admins': network_admins,
            'monitors': monitors,
            'alert_managers': alert_managers,
            'recent_activities': recent_activities,
            'api_users': api_users,
            'verified_users': queryset.filter(is_verified=True).count(),
            'two_factor_enabled': queryset.filter(two_factor_enabled=True).count(),
        }
        
        serializer = UserStatsSerializer(data=stats_data)
        serializer.is_valid()
        
        return success_response(serializer.data, "Statistiques utilisateurs récupérées")
    
    @action(detail=True, methods=['get'])
    def check_permissions(self, request, pk=None):
        """
        Vérifie les permissions OLT d'un utilisateur
        """
        user = self.get_object()
        
        # Vérification des permissions
        if not request.user.is_admin and request.user.id != user.id:
            return forbidden_response(
                "Vous n'avez pas accès à ces informations",
                required_permission="is_admin"
            )
        
        data = {
            'can_manage_olts': user.can_manage_olts,
            'can_view_olts': user.can_view_olts,
            'can_monitor_olts': user.can_monitor_olts,
            'can_manage_alerts': user.can_manage_alerts,
            'can_view_alerts': user.can_view_alerts,
            'can_run_diagnostics': user.can_run_diagnostics,
            'can_configure_snmp': user.can_configure_snmp,
            'can_view_analytics': user.can_view_analytics,
            'can_view_notifications': user.can_view_notifications,
            'can_manage_notifications': user.can_manage_notifications,
            'can_export_data': user.can_export_data,
            'permissions': {
                'olts': "Gestion des OLT" if not user.can_manage_olts else None,
                'alerts': "Gestion des alertes" if not user.can_manage_alerts else None,
                'diagnostics': "Diagnostics" if not user.can_run_diagnostics else None,
            }
        }
        
        return success_response(data, "Permissions OLT récupérées")
    
    @action(detail=False, methods=['get'])
    def activity_stats(self, request):
        """
        Statistiques d'activité dans le temps
        """
        if not request.user.is_admin:
            return forbidden_response(
                "Accès administrateur requis",
                required_permission="is_admin"
            )
        
        days = int(request.query_params.get('days', 7))
        cutoff = timezone.now() - timedelta(days=days)
        
        activities = UserActivity.objects.filter(created_at__gte=cutoff)
        
        # Groupement par jour
        from django.db.models.functions import TruncDate
        daily_stats = activities.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            by_action=Count('action'),
            by_severity=Count('severity')
        ).order_by('date')
        
        # Groupement par action
        by_action = dict(
            activities.values_list('action').annotate(count=Count('id'))
        )
        
        # Groupement par sévérité
        by_severity = dict(
            activities.values_list('severity').annotate(count=Count('id'))
        )
        
        total = activities.count()
        success_rate = activities.filter(success=True).count() / total if total > 0 else 0
        
        data = {
            'period': f"Derniers {days} jours",
            'total': total,
            'daily': list(daily_stats),
            'by_action': by_action,
            'by_severity': by_severity,
            'success_rate': round(success_rate * 100, 1)
        }
        
        return success_response(data, "Statistiques d'activité récupérées")
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def bulk_delete(self, request):
        """
        SuperAdmin : Suppression multiple d'utilisateurs
        """
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return error_response(
                "Aucun ID utilisateur fourni",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Empêcher l'auto-suppression
        if request.user.id in user_ids:
            return error_response(
                "Vous ne pouvez pas supprimer votre propre compte",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = User.objects.filter(id__in=user_ids).delete()[0]
        
        # Journalisation de l'activité
        UserActivity.objects.create(
            user=request.user,
            action='delete',
            severity='high',
            description=f"Suppression multiple de {deleted_count} utilisateurs",
            metadata={'user_ids': user_ids},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(
            {'deleted_count': deleted_count},
            f"{deleted_count} utilisateurs supprimés avec succès"
        )

    @action(detail=False, methods=['get'])
    def not_found_example(self, request):
        """
        Exemple d'utilisation de not_found_response
        """
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                serializer = UserMinimalSerializer(user)
                return success_response(serializer.data, "Utilisateur trouvé")
            except User.DoesNotExist:
                return not_found_response(
                    "Utilisateur non trouvé",
                    resource_type="user",
                    resource_id=user_id
                )
        
        return error_response("ID utilisateur requis", status_code=status.HTTP_400_BAD_REQUEST)


class TeamViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des équipes OLT
    """
    
    queryset = Team.objects.all().select_related('team_lead').prefetch_related('members')
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TeamFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """
        Filtre les équipes selon l'utilisateur
        """
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return Team.objects.none()
        
        # Admin voit toutes les équipes
        if user.is_admin:
            return Team.objects.all()
        
        # Les autres ne voient que leurs équipes
        return user.teams.all()
    
    def perform_create(self, serializer):
        """
        Crée une équipe et journalise l'activité
        """
        team = serializer.save()
        
        UserActivity.objects.create(
            user=self.request.user,
            action='create',
            description=f"Équipe OLT {team.name} créée",
            resource_type='team',
            resource_id=str(team.id),
            resource_name=team.name,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """
        Ajoute un membre à l'équipe
        """
        team = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return not_found_response(
                "Utilisateur non trouvé",
                resource_type="user",
                resource_id=user_id
            )
        
        team.members.add(user)
        
        # Journalisation
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description=f"{user.email} ajouté à l'équipe OLT {team.name}",
            resource_type='team',
            resource_id=str(team.id),
            resource_name=team.name,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(
            TeamSerializer(team).data,
            f"{user.email} ajouté à l'équipe"
        )
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """
        Retire un membre de l'équipe
        """
        team = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return not_found_response(
                "Utilisateur non trouvé",
                resource_type="user",
                resource_id=user_id
            )
        
        team.members.remove(user)
        
        # Journalisation
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description=f"{user.email} retiré de l'équipe OLT {team.name}",
            resource_type='team',
            resource_id=str(team.id),
            resource_name=team.name,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        return success_response(
            TeamSerializer(team).data,
            f"{user.email} retiré de l'équipe"
        )


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des rôles OLT
    """
    
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RoleFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def perform_create(self, serializer):
        """
        Crée un rôle et journalise l'activité
        """
        role = serializer.save()
        
        UserActivity.objects.create(
            user=self.request.user,
            action='create',
            description=f"Rôle OLT {role.name} créé",
            resource_type='role',
            resource_id=str(role.id),
            resource_name=role.name,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les permissions (lecture seule)
    """
    
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PermissionFilter
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['category', 'code', 'name']
    ordering = ['category', 'code']
    
    @action(detail=False, methods=['get'])
    def grouped(self, request):
        """
        Permissions groupées par catégorie
        """
        permissions = self.get_queryset()
        
        grouped = {}
        for category, _ in Permission.CATEGORY_CHOICES:
            perms = permissions.filter(category=category)
            if perms.exists():
                grouped[category] = PermissionSerializer(perms, many=True).data
        
        return success_response(grouped, "Permissions OLT groupées par catégorie")


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour les activités utilisateur (lecture seule)
    """
    
    queryset = UserActivity.objects.all().select_related('user')
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserActivityFilter
    search_fields = ['description', 'resource_type', 'ip_address']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filtre les activités selon l'utilisateur
        """
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return UserActivity.objects.none()
        
        # SuperAdmin voit tout
        if user.is_superadmin:
            return UserActivity.objects.all()
        
        # Admin voit tout
        if user.is_admin:
            return UserActivity.objects.all()
        
        # Les autres ne voient que leurs activités
        return UserActivity.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Activités récentes (dernières 24h)
        """
        last_24h = timezone.now() - timedelta(hours=24)
        activities = self.get_queryset().filter(created_at__gte=last_24h)[:50]
        
        serializer = self.get_serializer(activities, many=True)
        return success_response(serializer.data, "Activités récentes récupérées")
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """
        Activités groupées par utilisateur
        """
        if not request.user.is_admin:
            return forbidden_response(
                "Accès administrateur requis",
                required_permission="is_admin"
            )
        
        from django.db.models import Count
        
        activities = self.get_queryset().values(
            'user__email', 'user__first_name', 'user__last_name', 'user__role'
        ).annotate(
            count=Count('id'),
            last_activity=Count('created_at')
        ).order_by('-count')[:20]
        
        return success_response(list(activities), "Activités par utilisateur")
    
    @action(detail=False, methods=['get'])
    def by_action(self, request):
        """
        Activités groupées par action
        """
        if not request.user.is_admin:
            return forbidden_response(
                "Accès administrateur requis",
                required_permission="is_admin"
            )
        
        activities = self.get_queryset().values('action').annotate(
            count=Count('id'),
            avg_severity=Count('severity')
        ).order_by('-count')
        
        return success_response(list(activities), "Activités par action")
