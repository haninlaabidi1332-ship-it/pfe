# apps/core/models.py
"""
Core abstract base models for OLT Supervision platform.
"""
import uuid
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    """Abstract base model with created_at and updated_at timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimestampedModel):
    """
    Standard base model: UUID PK + timestamps.
    Base class for all models in OLT Supervision.
    """
    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(BaseModel):
    """Adds soft-delete support."""
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    class Meta:
        abstract = True


class Config(BaseModel):
    """
    Configuration globale de la plateforme de supervision OLT.
    Stocke les paramètres système, seuils d'alertes, intégrations, etc.
    """
    
    CONFIG_TYPES = [
        ('general', '⚙️ Général'),
        ('security', '🛡️ Sécurité'),
        ('snmp', '📡 SNMP'),
        ('monitoring', '📊 Monitoring'),
        ('alerts', '⚠️ Alertes'),
        ('notifications', '🔔 Notifications'),
        ('integrations', '🔌 Intégrations (Slack, Teams, etc.)'),
        ('thresholds', '📈 Seuils de performance'),
        ('scheduling', '⏰ Planification'),
        ('logging', '📝 Journalisation'),
    ]
    
    key = models.CharField('Clé', max_length=200, unique=True)
    value = models.JSONField('Valeur', default=dict)
    description = models.TextField('Description', blank=True)
    config_type = models.CharField('Type', max_length=20, choices=CONFIG_TYPES, default='general')
    is_encrypted = models.BooleanField('Chiffré', default=False)
    
    class Meta:
        db_table = 'core_config'
        verbose_name = 'Configuration'
        verbose_name_plural = 'Configurations'
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['config_type']),
        ]
    
    def __str__(self):
        return f"{self.key} ({self.get_config_type_display()})"
    
    def save(self, *args, **kwargs):
        # Invalider le cache
        from django.core.cache import cache
        cache.delete(f'config_{self.key}')
        cache.delete('config_all')
        super().save(*args, **kwargs)