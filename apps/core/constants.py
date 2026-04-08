# apps/core/constants.py
"""
Constantes globales pour la plateforme OLT Supervision
"""

# ============================================================================
# MÉTHODES HTTP (conservées)
# ============================================================================
HTTP_METHODS = {
    'GET': 'GET',
    'POST': 'POST',
    'PUT': 'PUT',
    'PATCH': 'PATCH',
    'DELETE': 'DELETE',
    'OPTIONS': 'OPTIONS',
    'HEAD': 'HEAD',
}

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']

# ============================================================================
# INFORMATIONS DE LA PLATEFORME
# ============================================================================
PLATFORM = {
    'name': 'OLT Supervision',
    'version': '1.0.0',
    'description': 'Plateforme de supervision d’équipements OLT',
    'website': 'https://oltsupervision.io',
    'company': 'OLT Supervision Solutions',
    'support_email': 'support@oltsupervision.io',
}

# ============================================================================
# PAGINATION ET CACHE
# ============================================================================
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

CACHE_TTL = {
    'short': 60,           # 1 minute
    'medium': 300,         # 5 minutes
    'long': 3600,          # 1 heure
    'day': 86400,          # 1 jour
    'week': 604800,        # 1 semaine
    'month': 2592000,      # 30 jours
}

# ============================================================================
# STATUTS DES OLT
# ============================================================================
OLT_STATUS = {
    'active': '✅ Actif',
    'maintenance': '🔧 Maintenance',
    'degraded': '⚠️ Dégradé',
    'down': '❌ Hors service',
    'unknown': '❓ Inconnu',
}

# ============================================================================
# STATUTS DES ALERTES
# ============================================================================
ALERT_STATUS = {
    'pending': '⏳ En attente',
    'acknowledged': '👀 Acquittée',
    'resolved': '✅ Résolue',
    'ignored': '🚫 Ignorée',
}

# ============================================================================
# SÉVÉRITÉ DES ALERTES
# ============================================================================
ALERT_SEVERITY = {
    'info': 'ℹ️ Info',
    'warning': '⚠️ Avertissement',
    'critical': '🔴 Critique',
    'emergency': '🆘 Urgence',
}

# ============================================================================
# TYPES DE MÉTRIQUES SNMP
# ============================================================================
METRIC_TYPES = {
    'cpu': '🖥️ CPU (%)',
    'memory': '💾 Mémoire (%)',
    'temperature': '🌡️ Température (°C)',
    'rx_power': '📡 Puissance RX (dBm)',
    'tx_power': '📡 Puissance TX (dBm)',
    'packet_loss': '📉 Perte paquets (%)',
    'latency': '⏱️ Latence (ms)',
    'link_status': '🔗 État du lien',
}

# ============================================================================
# TYPES D'ÉQUIPEMENTS
# ============================================================================
EQUIPMENT_TYPES = {
    'olt': '📡 OLT',
    'switch': '🔌 Switch',
    'router': '🌐 Routeur',
    'splitter': '🔀 Splitter',
}

# ============================================================================
# PROTOCOLES DE SUPERVISION
# ============================================================================
MONITORING_PROTOCOLS = {
    'snmp': 'SNMP',
    'bfd': 'BFD',
    'icmp': 'ICMP (ping)',
    'netconf': 'NETCONF',
}

# ============================================================================
# FRÉQUENCES DE COLLECTE (secondes)
# ============================================================================
COLLECTION_FREQUENCIES = {
    'realtime': 10,
    'high': 30,
    'normal': 60,
    'low': 300,
    'off': 0,
}

# ============================================================================
# SEUILS PAR DÉFAUT POUR LES ANOMALIES
# ============================================================================
DEFAULT_THRESHOLDS = {
    'cpu': 85.0,
    'memory': 90.0,
    'temperature': 75.0,
    'rx_power': -25.0,
    'tx_power': -2.0,
    'packet_loss': 1.0,
    'latency': 50.0,
}

# ============================================================================
# NOMS D'ÉVÉNEMENTS POUR LE JOURNAL
# ============================================================================
EVENT_TYPES = {
    'olt_created': '🏷️ OLT créé',
    'olt_updated': '✏️ OLT modifié',
    'olt_deleted': '🗑️ OLT supprimé',
    'snmp_collection_started': '🔄 Début collecte SNMP',
    'snmp_collection_completed': '✅ Collecte SNMP terminée',
    'snmp_collection_failed': '❌ Échec collecte SNMP',
    'bfd_status_changed': '🔄 Changement état BFD',
    'anomaly_detected': '🔍 Anomalie détectée',
    'alert_created': '⚠️ Alerte créée',
    'alert_acknowledged': '👀 Alerte acquittée',
    'alert_resolved': '✅ Alerte résolue',
}

# ============================================================================
# RÔLES UTILISATEUR (supervision)
# ============================================================================
USER_ROLES = {
    'superadmin': '👑 Super administrateur',
    'network_admin': '🌐 Administrateur réseau',
    'monitor': '📊 Superviseur',
    'viewer': '👀 Observateur',
}