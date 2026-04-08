# apps/users/apps.py
"""
Configuration de l'application users pour OLT Supervision
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = '👥 Users - Gestion des utilisateurs OLT Supervision'

    def ready(self):
        # Importer les signaux
        try:
            import apps.users.signals
        except ImportError:
            pass
