# apps/core/signals.py
"""
Signaux Django pour l'application core OLT Supervision
"""
import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone

from .models import Config

logger = logging.getLogger(__name__)


# ============================================================================
# SIGNAUX POUR LE MODÈLE CONFIG
# ============================================================================

@receiver(post_save, sender=Config)
def config_post_save(sender, instance, created, **kwargs):
    """
    Signal après la sauvegarde d'une configuration
    """
    action = "créée" if created else "modifiée"
    logger.info(f"🔧 Configuration '{instance.key}' {action}")
    
    # Invalider le cache pour cette clé
    cache_key = f"config_{instance.key}"
    cache.delete(cache_key)
    
    # Invalider aussi le cache global des configurations
    cache.delete("config_all")
    cache.delete_pattern("config_*")


@receiver(pre_save, sender=Config)
def config_pre_save(sender, instance, **kwargs):
    """
    Signal avant la sauvegarde d'une configuration
    """
    if instance.pk:
        try:
            old_instance = Config.objects.get(pk=instance.pk)
            if old_instance.value != instance.value:
                logger.debug(f"📝 Configuration '{instance.key}' va être modifiée")
                logger.debug(f"   Ancienne valeur: {old_instance.value}")
                logger.debug(f"   Nouvelle valeur: {instance.value}")
        except Config.DoesNotExist:
            pass


@receiver(post_delete, sender=Config)
def config_post_delete(sender, instance, **kwargs):
    """
    Signal après la suppression d'une configuration
    """
    logger.info(f"🗑️ Configuration '{instance.key}' supprimée")
    
    # Invalider le cache
    cache_key = f"config_{instance.key}"
    cache.delete(cache_key)
    cache.delete_pattern("config_*")


# ============================================================================
# SIGNAUX POUR LE CACHE
# ============================================================================

@receiver(post_save, sender=Config)
@receiver(post_delete, sender=Config)
def invalidate_config_cache(sender, **kwargs):
    """
    Invalide le cache des configurations
    """
    cache.delete("config_all")
    cache.delete_pattern("config_*")
    logger.debug("🧹 Cache des configurations invalidé")


# ============================================================================
# SIGNAUX POUR L'AUDIT (optionnel)
# ============================================================================

def log_config_change(user, action, config_key, old_value=None, new_value=None):
    """
    Fonction utilitaire pour journaliser les changements de configuration
    """
    try:
        from apps.users.models import UserActivity
        
        UserActivity.objects.create(
            user=user,
            action=f"config_{action}",
            target=f"config:{config_key}",
            details={
                'old_value': old_value,
                'new_value': new_value,
            },
            severity='low'
        )
    except ImportError:
        # L'app users n'est pas encore installée
        pass
    except Exception as e:
        logger.error(f"Erreur lors de l'audit: {e}")


# ============================================================================
# INITIALISATION DES SIGNAUX
# ============================================================================

def connect_signals():
    """
    Connecte manuellement les signaux (si nécessaire)
    """
    logger.info("🔌 Signaux core OLT Supervision connectés")


# Connecter les signaux au chargement
connect_signals()