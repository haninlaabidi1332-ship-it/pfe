# apps/core/mixins.py
"""
Mixins complets pour la plateforme OLT Supervision
- Audit et journalisation
- Suppression logique
- Actions groupées
- Export de données
- Gestion du cache
- Permissions avancées
- Métriques et performances
"""
import logging
import json
from django.db import models
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from .responses import (
    success_response, error_response, validation_error_response, 
    created_response, not_found_response
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================================
# MIXINS DE MODÈLES
# ============================================================================

class AuditMixin(models.Model):
    """
    Mixin pour l'audit complet des modèles
    - Suivi des créateurs/modificateurs
    - Journalisation automatique
    """
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='Créé par'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='Modifié par'
    )
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        if request and request.user and request.user.is_authenticated:
            if not self.pk:
                self.created_by = request.user
            self.updated_by = request.user
        super().save(*args, **kwargs)
    
    def log_action(self, action, request=None, details=None):
        """
        Journalise une action sur l'objet
        """
        try:
            from apps.users.models import UserActivity
            UserActivity.objects.create(
                user=request.user if request else None,
                action=action,
                severity='medium' if action in ['update', 'delete'] else 'low',
                description=f"{action.title()} {self.__class__.__name__}: {str(self)}",
                resource_type=self.__class__.__name__,
                resource_id=str(self.pk),
                metadata=details or {},
                ip_address=request.META.get('REMOTE_ADDR') if request else None,
                success=True
            )
        except Exception as e:
            logger.error(f"Audit log failed: {e}")


class SoftDeleteMixin(models.Model):
    """
    Mixin pour la suppression logique avec restauration
    """
    is_deleted = models.BooleanField('Supprimé', default=False)
    deleted_at = models.DateTimeField('Supprimé le', null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name='Supprimé par'
    )
    
    objects = models.Manager()
    active_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, user=None):
        """Suppression logique"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def hard_delete(self):
        """Suppression physique définitive"""
        super().delete()
    
    def restore(self):
        """Restaure un élément supprimé logiquement"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class VersionedMixin(models.Model):
    """
    Mixin pour le versionnage des données
    - Suivi des versions
    - Historique des modifications
    """
    version = models.IntegerField('Version', default=1)
    version_history = models.JSONField('Historique des versions', default=list, blank=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if self.pk:
            # Sauvegarder l'état actuel dans l'historique
            old_state = {}
            for field in self._meta.fields:
                if field.name not in ['id', 'version', 'version_history', 'created_at', 'updated_at']:
                    old_state[field.name] = getattr(self, field.name)
            
            history_entry = {
                'version': self.version,
                'timestamp': timezone.now().isoformat(),
                'data': old_state
            }
            self.version_history = [history_entry] + (self.version_history or [])[:99]  # Garder 100 versions
            self.version += 1
        super().save(*args, **kwargs)
    
    def get_version(self, version_number):
        """Récupère une version spécifique"""
        for entry in self.version_history or []:
            if entry.get('version') == version_number:
                return entry.get('data')
        return None


class OrderableMixin(models.Model):
    """
    Mixin pour l'ordonnancement avec réorganisation automatique
    """
    order = models.IntegerField('Ordre', default=0)
    
    class Meta:
        abstract = True
        ordering = ['order']
    
    def save(self, *args, **kwargs):
        if not self.pk and self.order == 0:
            # Assigner le prochain ordre disponible
            last_order = self.__class__.objects.aggregate(models.Max('order'))['order__max'] or 0
            self.order = last_order + 1
        super().save(*args, **kwargs)
    
    def move_up(self):
        """Déplace l'élément vers le haut"""
        if self.order > 1:
            previous = self.__class__.objects.filter(order=self.order - 1).first()
            if previous:
                previous.order = self.order
                previous.save()
                self.order -= 1
                self.save()
    
    def move_down(self):
        """Déplace l'élément vers le bas"""
        next_item = self.__class__.objects.filter(order=self.order + 1).first()
        if next_item:
            next_item.order = self.order
            next_item.save()
            self.order += 1
            self.save()


class TimeStampedMixin(models.Model):
    """
    Mixin pour les timestamps avec gestion de fuseau
    """
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        abstract = True


class CacheableMixin(models.Model):
    """
    Mixin pour la gestion du cache des modèles
    """
    cache_prefix = 'model:'
    cache_timeout = 3600  # 1 heure
    
    class Meta:
        abstract = True
    
    def get_cache_key(self, suffix=''):
        return f"{self.cache_prefix}{self.__class__.__name__.lower()}:{self.pk}{suffix}"
    
    def invalidate_cache(self):
        """Invalide le cache pour ce modèle"""
        cache.delete_pattern(f"{self.cache_prefix}{self.__class__.__name__.lower()}:*")
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invalidate_cache()
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.invalidate_cache()


# ============================================================================
# MIXINS DE VUES
# ============================================================================

class AuditLogMixin:
    """
    Mixin pour journaliser automatiquement les actions CRUD
    """
    
    def perform_create(self, serializer):
        instance = serializer.save()
        self._log_action('create', instance)
        return instance
    
    def perform_update(self, serializer):
        instance = serializer.save()
        self._log_action('update', instance)
        return instance
    
    def perform_destroy(self, instance):
        self._log_action('delete', instance)
        if hasattr(instance, 'delete'):
            instance.delete(user=self.request.user)
        else:
            instance.delete()
    
    def _log_action(self, action, instance):
        try:
            from apps.users.models import UserActivity
            UserActivity.objects.create(
                user=self.request.user,
                action=action,
                severity='medium' if action in ['update', 'delete'] else 'low',
                description=f"{action.title()} {instance.__class__.__name__}: {str(instance)}",
                resource_type=instance.__class__.__name__,
                resource_id=str(instance.pk),
                metadata={
                    'model': instance.__class__.__name__,
                    'action': action,
                    'timestamp': timezone.now().isoformat()
                },
                ip_address=self.request.META.get('REMOTE_ADDR'),
                request_method=self.request.method,
                request_path=self.request.path,
                success=True,
            )
        except Exception as e:
            logger.error(f"Audit log failed: {e}")


class OwnerFilterMixin:
    """
    Mixin pour filtrer par propriétaire
    - Admin voit tout
    - Utilisateurs voient leurs propres données
    """
    owner_field = 'created_by'
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return qs.none()
        
        if user.is_superuser or getattr(user, 'is_admin', False):
            return qs
        
        return qs.filter(**{self.owner_field: user})


class SoftDeleteViewMixin:
    """
    Mixin pour supporter la suppression logique dans les ViewSets
    """
    
    def get_queryset(self):
        """Exclut les éléments supprimés par défaut"""
        qs = super().get_queryset()
        if hasattr(qs.model, 'is_deleted'):
            return qs.filter(is_deleted=False)
        return qs
    
    def perform_destroy(self, instance):
        """Suppression logique"""
        if hasattr(instance, 'delete'):
            instance.delete(user=self.request.user)
        else:
            instance.delete()
    
    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, pk=None):
        """Restaure un élément supprimé logiquement"""
        instance = self.get_queryset().model.all_objects.filter(pk=pk).first()
        
        if not instance:
            return not_found_response("Élément non trouvé")
        
        if not instance.is_deleted:
            return error_response("Cet élément n'est pas supprimé", status_code=400)
        
        if hasattr(instance, 'restore'):
            instance.restore()
        else:
            instance.is_deleted = False
            instance.deleted_at = None
            instance.save()
        
        return success_response(
            self.get_serializer(instance).data,
            "Élément restauré avec succès"
        )


class BulkActionViewMixin:
    """
    Mixin pour les actions groupées
    """
    bulk_update_fields = []  # À surcharger dans la sous-classe
    
    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        """Suppression groupée"""
        ids = request.data.get('ids', [])
        if not ids:
            return error_response("Aucun ID fourni", status_code=400)
        
        queryset = self.get_queryset().filter(id__in=ids)
        count = queryset.count()
        
        if count == 0:
            return error_response("Aucun élément trouvé", status_code=404)
        
        for obj in queryset:
            self.perform_destroy(obj)
        
        return success_response(
            {'deleted_count': count},
            f"{count} élément(s) supprimé(s)"
        )
    
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        """Mise à jour groupée"""
        ids = request.data.get('ids', [])
        fields = request.data.get('fields', {})
        
        if not ids or not fields:
            return error_response("ids et fields sont requis", status_code=400)
        
        # Filtrer les champs autorisés
        safe_fields = {k: v for k, v in fields.items() if k in self.bulk_update_fields}
        
        if not safe_fields:
            return error_response("Aucun champ valide à mettre à jour", status_code=400)
        
        count = self.get_queryset().filter(id__in=ids).update(**safe_fields)
        
        return success_response(
            {'updated_count': count},
            f"{count} élément(s) mis à jour"
        )
    
    @action(detail=False, methods=['post'], url_path='bulk-status')
    def bulk_status(self, request):
        """Mise à jour groupée du statut"""
        ids = request.data.get('ids', [])
        status_value = request.data.get('status')
        
        if not ids or not status_value:
            return error_response("ids et status sont requis", status_code=400)
        
        count = self.get_queryset().filter(id__in=ids).update(status=status_value)
        
        return success_response(
            {'updated_count': count},
            f"{count} élément(s) mis à jour"
        )


class CachedQueryMixin:
    """
    Mixin pour le cache des requêtes
    """
    cache_timeout = 300  # 5 minutes
    cache_key_prefix = 'view'
    cache_enabled = True
    
    def get_cache_key(self, request):
        """Génère une clé de cache unique"""
        user_id = request.user.id if request.user.is_authenticated else 'anon'
        params = request.query_params.urlencode()
        return f"{self.cache_key_prefix}:{user_id}:{request.path}:{params}"
    
    def list(self, request, *args, **kwargs):
        """Liste avec cache"""
        if self.cache_enabled and request.method in ['GET', 'HEAD']:
            cache_key = self.get_cache_key(request)
            cached_response = cache.get(cache_key)
            
            if cached_response is not None:
                return Response(cached_response)
            
            response = super().list(request, *args, **kwargs)
            cache.set(cache_key, response.data, self.cache_timeout)
            return response
        
        return super().list(request, *args, **kwargs)
    
    def invalidate_cache(self):
        """Invalide le cache pour cette vue"""
        pattern = f"{self.cache_key_prefix}:*"
        cache.delete_pattern(pattern)


class ExportMixin:
    """
    Mixin pour l'export de données
    """
    export_formats = ['csv', 'json', 'excel']
    
    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """Export des données"""
        export_format = request.query_params.get('format', 'csv')
        
        if export_format not in self.export_formats:
            return error_response(
                f"Format non supporté. Choisir parmi: {', '.join(self.export_formats)}",
                status_code=400
            )
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        if not data:
            return error_response("Aucune donnée à exporter", status_code=404)
        
        try:
            import pandas as pd
            from io import BytesIO, StringIO
            from django.http import HttpResponse
            
            df = pd.DataFrame(data)
            
            if export_format == 'excel':
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Data', index=False)
                output.seek(0)
                response = HttpResponse(
                    output.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="export_{timezone.now().date()}.xlsx"'
                return response
            
            elif export_format == 'json':
                json_data = df.to_json(orient='records', indent=2, date_format='iso')
                response = HttpResponse(json_data, content_type='application/json')
                response['Content-Disposition'] = f'attachment; filename="export_{timezone.now().date()}.json"'
                return response
            
            else:  # csv
                csv_data = df.to_csv(index=False)
                response = HttpResponse(csv_data, content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="export_{timezone.now().date()}.csv"'
                return response
                
        except ImportError as e:
            return error_response(f"Bibliothèque manquante: {str(e)}", status_code=500)
        except Exception as e:
            return error_response(f"Erreur d'export: {str(e)}", status_code=500)


class StatisticsMixin:
    """
    Mixin pour les statistiques
    """
    
    def get_statistics(self, queryset):
        """
        Surcharger dans la sous-classe pour des stats personnalisées
        """
        return {'total': queryset.count()}
    
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """Endpoint de statistiques"""
        queryset = self.filter_queryset(self.get_queryset())
        stats = self.get_statistics(queryset)
        return success_response(stats, "Statistiques récupérées")


# ============================================================================
# MIXINS DE SÉRIALISEURS
# ============================================================================

class DynamicFieldsMixin:
    """
    Mixin pour les champs dynamiques (select fields)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        request = self.context.get('request')
        if request:
            fields = request.query_params.get('fields')
            exclude = request.query_params.get('exclude')
            
            if fields:
                allowed = set(fields.split(','))
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
            
            if exclude:
                not_allowed = set(exclude.split(','))
                for field_name in not_allowed:
                    self.fields.pop(field_name, None)


class NestedValidationMixin:
    """
    Mixin pour la validation des données imbriquées
    """
    
    def validate_nested(self, data, nested_serializers):
        """
        Valide les champs imbriqués
        """
        errors = {}
        
        for field_name, serializer_class in nested_serializers.items():
            if field_name in data:
                nested_data = data[field_name]
                if isinstance(nested_data, list):
                    for i, item in enumerate(nested_data):
                        serializer = serializer_class(data=item)
                        if not serializer.is_valid():
                            errors[f"{field_name}[{i}]"] = serializer.errors
                else:
                    serializer = serializer_class(data=nested_data)
                    if not serializer.is_valid():
                        errors[field_name] = serializer.errors
        
        if errors:
            raise validation_error_response(errors)
        
        return data


# ============================================================================
# MIXINS DE PERMISSIONS
# ============================================================================

class PermissionMixin:
    """
    Mixin pour la gestion des permissions
    """
    permission_map = {}
    
    def get_permission_required(self, action):
        """Retourne la permission requise pour une action"""
        return self.permission_map.get(action, f"{self.model_name}.view_{self.model_name}")
    
    def check_permission(self, request, action, obj=None):
        """Vérifie si l'utilisateur a la permission"""
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        permission = self.get_permission_required(action)
        
        if obj:
            return request.user.has_perm(permission, obj)
        return request.user.has_perm(permission)
    
    def has_view_permission(self, request, view):
        """Vérifie la permission de visualisation"""
        return self.check_permission(request, 'view')
    
    def has_add_permission(self, request, view):
        """Vérifie la permission d'ajout"""
        return self.check_permission(request, 'add')
    
    def has_change_permission(self, request, view, obj=None):
        """Vérifie la permission de modification"""
        return self.check_permission(request, 'change', obj)
    
    def has_delete_permission(self, request, view, obj=None):
        """Vérifie la permission de suppression"""
        return self.check_permission(request, 'delete', obj)


# ============================================================================
# MIXINS DE PERFORMANCE (adaptés pour OLT)
# ============================================================================

class MetricsMixin:
    """
    Mixin pour la collecte de métriques de performance
    (à adapter selon votre modèle de monitoring, ici simple log)
    """
    
    def record_metric(self, metric_name, value, tags=None):
        """Enregistre une métrique (log simple)"""
        logger.info(f"METRIC: {metric_name}={value} tags={tags}")
        # Optionnel : stocker dans une base de données dédiée
    
    def record_query_performance(self, query_name, duration_ms, rows_affected=None):
        """Enregistre les performances d'une requête"""
        self.record_metric(
            f"query_{query_name}_duration",
            duration_ms,
            {'rows': rows_affected, 'query': query_name}
        )
    
    def record_api_call(self, endpoint, method, duration_ms, status_code):
        """Enregistre un appel API"""
        self.record_metric(
            "api_call_duration",
            duration_ms,
            {'endpoint': endpoint, 'method': method, 'status_code': status_code}
        )


class PerformanceMixin:
    """
    Mixin pour le monitoring des performances
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Mesure le temps d'exécution"""
        start_time = timezone.now()
        response = super().dispatch(request, *args, **kwargs)
        duration = (timezone.now() - start_time).total_seconds() * 1000
        
        # Log des requêtes lentes
        if duration > 1000:  # Plus d'1 seconde
            logger.warning(
                f"Slow request: {request.method} {request.path} - {duration:.2f}ms"
            )
        
        # Ajouter le temps d'exécution dans les headers
        response['X-Query-Time-Ms'] = int(duration)
        
        return response


# ============================================================================
# MIXINS DE VALIDATION
# ============================================================================

class ValidationMixin:
    """
    Mixin pour la validation des données
    """
    
    def validate_required_fields(self, data, required_fields):
        """Valide que tous les champs requis sont présents"""
        missing = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing.append(field)
        
        if missing:
            raise validation_error_response(
                {field: 'Ce champ est requis' for field in missing}
            )
        
        return data
    
    def validate_data_type(self, value, expected_type):
        """Valide le type de données"""
        if value is None:
            return value
        
        if not isinstance(value, expected_type):
            raise validation_error_response(
                {'type': f"Type attendu: {expected_type.__name__}, reçu: {type(value).__name__}"}
            )
        
        return value


# ============================================================================
# MIXINS DE TESTS
# ============================================================================

class TestMixin:
    """
    Mixin pour les tests unitaires (adapté OLT)
    """
    
    def create_test_user(self, **kwargs):
        """Crée un utilisateur de test"""
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': 'viewer',
            'status': 'active'
        }
        defaults.update(kwargs)
        
        return User.objects.create_user(**defaults)
    
    def create_test_admin(self, **kwargs):
        """Crée un administrateur de test"""
        defaults = {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'admin123',
            'role': 'superadmin',
            'status': 'active'
        }
        defaults.update(kwargs)
        
        return User.objects.create_superuser(**defaults)
    
    def create_test_olt(self, **kwargs):
        """Crée un OLT de test (si l'application olt_inventory est disponible)"""
        try:
            from apps.olt_inventory.models import OLT
            defaults = {
                'name': 'Test OLT',
                'ip_address': '192.168.1.1',
                'snmp_community': 'public',
                'status': 'active'
            }
            defaults.update(kwargs)
            return OLT.objects.create(**defaults)
        except ImportError:
            return None
    
    def assertResponseSuccess(self, response, expected_message=None):
        """Vérifie que la réponse est un succès"""
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('status'))
        if expected_message:
            self.assertEqual(response.data.get('message'), expected_message)
    
    def assertResponseError(self, response, expected_code=None, expected_message=None):
        """Vérifie que la réponse est une erreur"""
        self.assertFalse(response.data.get('status'))
        if expected_code:
            self.assertEqual(response.data.get('code'), expected_code)
        if expected_message:
            self.assertEqual(response.data.get('message'), expected_message)
    
    def assertResponseCreated(self, response, expected_message=None):
        """Vérifie que la réponse est 201 Created"""
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data.get('status'))
        if expected_message:
            self.assertEqual(response.data.get('message'), expected_message)