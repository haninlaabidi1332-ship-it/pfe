# apps/olt_inventory/apps.py

from django.apps import AppConfig

class OltInventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # CHANGE CETTE LIGNE :
    name = 'apps.olt_inventory'