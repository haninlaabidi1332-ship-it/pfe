# apps/users/signals.py
"""
Signaux Django pour l'application users OLT Supervision
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
import logging

from .models import User, UserActivity

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    """Gestionnaire de connexion"""
    user.last_login = timezone.now()
    user.last_login_ip = request.META.get('REMOTE_ADDR')
    user.save(update_fields=['last_login', 'last_login_ip'])
    
    UserActivity.objects.create(
        user=user,
        action='login',
        description=f"Connexion depuis {user.last_login_ip}",
        ip_address=user.last_login_ip,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        success=True
    )
    logger.info(f"Utilisateur {user.email} connecté")


@receiver(user_logged_out)
def handle_user_logout(sender, request, user, **kwargs):
    """Gestionnaire de déconnexion"""
    if user:
        UserActivity.objects.create(
            user=user,
            action='logout',
            description="Déconnexion",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        logger.info(f"Utilisateur {user.email} déconnecté")


@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance, created, **kwargs):
    """Gestionnaire après sauvegarde utilisateur"""
    if created:
        logger.info(f"Nouvel utilisateur créé: {instance.email} (rôle: {instance.role})")
    else:
        logger.debug(f"Utilisateur mis à jour: {instance.email}")