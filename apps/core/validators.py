# apps/core/validators.py
"""
Validateurs complets pour la plateforme OLT Supervision
- Validation des expressions CRON
- Validation JSON/YAML
- Validation des adresses IP, hôtes, ports
- Validation des fichiers
- Validation des seuils et valeurs numériques
- Validation des emails, domaines, fuseaux horaires
"""
import re
import json
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


# ============================================================================
# CRON ET PLANIFICATION
# ============================================================================

def validate_cron_expression(value):
    """
    Valide une expression CRON pour les tâches planifiées (collecte SNMP, alertes, etc.)
    Supporte les formats 5 et 6 champs
    """
    if not value:
        return value
    
    parts = value.strip().split()
    if len(parts) not in [5, 6]:
        raise ValidationError(
            _("Format CRON invalide. Utilisez 5 ou 6 champs: minute hour day month weekday [year]"),
            code='invalid_cron_parts'
        )
    
    minute, hour, day, month, weekday = parts[:5]
    
    # Patterns pour chaque champ
    pattern = r'^(\*|\d+|\d+-\d+|\d+(,\d+)*)(/\d+)?$'
    
    if not re.match(pattern, minute):
        raise ValidationError(_(f"Champ minute invalide: {minute}"), code='invalid_cron_minute')
    if not re.match(pattern, hour):
        raise ValidationError(_(f"Champ heure invalide: {hour}"), code='invalid_cron_hour')
    if not re.match(pattern, day):
        raise ValidationError(_(f"Champ jour invalide: {day}"), code='invalid_cron_day')
    if not re.match(pattern, month):
        raise ValidationError(_(f"Champ mois invalide: {month}"), code='invalid_cron_month')
    if not re.match(pattern, weekday):
        raise ValidationError(_(f"Champ jour semaine invalide: {weekday}"), code='invalid_cron_weekday')
    
    return value


def validate_schedule_interval(value):
    """
    Valide un intervalle de planification
    """
    if not value:
        return value
    
    valid_intervals = ['minute', 'hour', 'day', 'week', 'month']
    
    if value not in valid_intervals:
        raise ValidationError(
            _(f"Intervalle invalide. Choisir parmi: {', '.join(valid_intervals)}"),
            code='invalid_interval'
        )
    
    return value


# ============================================================================
# JSON ET YAML
# ============================================================================

def validate_json_schema(value):
    """
    Valide un schéma JSON
    """
    if not value:
        return value
    
    try:
        if isinstance(value, str):
            json.loads(value)
        elif isinstance(value, (dict, list)):
            json.dumps(value)
        else:
            raise ValueError
    except (ValueError, TypeError, json.JSONDecodeError):
        raise ValidationError(
            _("La valeur doit être un JSON valide"),
            code='invalid_json'
        )
    
    return value


def validate_yaml_content(value):
    """
    Valide le contenu YAML
    """
    if not value or not value.strip():
        raise ValidationError(_("Le contenu ne peut pas être vide"), code='empty_yaml')
    
    try:
        import yaml
        parsed = yaml.safe_load(value)
        if parsed is None:
            raise ValidationError(_("Le contenu YAML est vide"), code='empty_parsed_yaml')
        return value
    except ImportError:
        # yaml non installé, validation basique
        if '---' in value or '...' in value:
            return value
        raise ValidationError(_("Contenu YAML invalide"), code='invalid_yaml')
    except Exception as e:
        raise ValidationError(_(f"Erreur de syntaxe YAML: {str(e)}"), code='yaml_error')


# ============================================================================
# HÔTES, IP, PORTS (spécifique réseau)
# ============================================================================

def validate_ip_address(value):
    """
    Valide une adresse IPv4 ou IPv6
    """
    if not value:
        return value
    
    import ipaddress
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        raise ValidationError(_("Adresse IP invalide"), code='invalid_ip')


def validate_hostname(value):
    """
    Valide un nom d'hôte ou une adresse IP
    """
    if not value:
        return value
    
    # IPv4
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # IPv6 (simplifié)
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    # Hostname
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not (re.match(ipv4_pattern, value) or re.match(ipv6_pattern, value) or re.match(hostname_pattern, value)):
        raise ValidationError(_("Nom d'hôte ou adresse IP invalide"), code='invalid_hostname')
    
    return value


def validate_port(value):
    """
    Valide un numéro de port (1-65535)
    """
    if value is None:
        return value
    
    try:
        port = int(value)
        if not (1 <= port <= 65535):
            raise ValueError
        return port
    except (ValueError, TypeError):
        raise ValidationError(_("Le port doit être un nombre entre 1 et 65535"), code='invalid_port')


# ============================================================================
# SNMP (spécifique)
# ============================================================================

def validate_snmp_community(value):
    """
    Valide une communauté SNMP (non vide, pas d'espaces, caractères simples)
    """
    if not value:
        raise ValidationError(_("La communauté SNMP ne peut pas être vide"), code='empty_snmp_community')
    
    if len(value) > 50:
        raise ValidationError(_("La communauté SNMP ne peut pas dépasser 50 caractères"), code='snmp_community_too_long')
    
    if any(c in value for c in ['\n', '\r', '\t', ' ']):
        raise ValidationError(_("La communauté SNMP ne doit pas contenir d'espaces ou de caractères de contrôle"), code='invalid_snmp_community_chars')
    
    return value


def validate_snmp_oid(value):
    """
    Valide un OID SNMP (ex: 1.3.6.1.2.1.1.1.0)
    """
    if not value:
        return value
    
    pattern = r'^(\d+\.)*\d+$'
    if not re.match(pattern, value):
        raise ValidationError(_("OID SNMP invalide. Format attendu: 1.3.6.1.2.1.1.1.0"), code='invalid_snmp_oid')
    
    return value


# ============================================================================
# FICHIERS
# ============================================================================

def validate_file_size(value, max_size_mb=10):
    """
    Valide la taille d'un fichier
    """
    if not value:
        return value
    
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            _(f"La taille du fichier ne doit pas dépasser {max_size_mb} MB"),
            code='file_too_large'
        )
    
    return value


def validate_file_extension(value, allowed_extensions=None):
    """
    Valide l'extension d'un fichier
    """
    if not value:
        return value
    
    allowed = allowed_extensions or ['.csv', '.json', '.xml', '.txt', '.log', '.pcap', '.cap']
    import os
    
    ext = os.path.splitext(value.name)[1].lower()
    
    if ext not in allowed:
        raise ValidationError(
            _(f"Extension de fichier non supportée. Extensions autorisées: {', '.join(allowed)}"),
            code='invalid_extension'
        )
    
    return value


# ============================================================================
# NUMÉRIQUES ET SEUILS
# ============================================================================

def validate_positive_integer(value):
    """
    Valide un entier positif
    """
    if value is None:
        return value
    
    try:
        val = int(value)
        if val <= 0:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un entier positif"), code='invalid_positive_integer')


def validate_non_negative_integer(value):
    """
    Valide un entier non négatif
    """
    if value is None:
        return value
    
    try:
        val = int(value)
        if val < 0:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un entier non négatif"), code='invalid_non_negative_integer')


def validate_percentage(value):
    """
    Valide un pourcentage (0-100)
    """
    if value is None:
        return value
    
    try:
        val = float(value)
        if val < 0 or val > 100:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("Le pourcentage doit être entre 0 et 100"), code='invalid_percentage')


def validate_threshold(value, min_val=None, max_val=None):
    """
    Valide un seuil avec bornes optionnelles
    """
    if value is None:
        return value
    
    try:
        val = float(value)
        if min_val is not None and val < min_val:
            raise ValidationError(_(f"La valeur doit être supérieure ou égale à {min_val}"), code='below_min')
        if max_val is not None and val > max_val:
            raise ValidationError(_(f"La valeur doit être inférieure ou égale à {max_val}"), code='above_max')
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un nombre"), code='invalid_number')


# ============================================================================
# CHAÎNES DE CARACTÈRES (identifiants, noms)
# ============================================================================

def validate_identifier(value):
    """
    Valide un identifiant (lettres, chiffres, underscore, tiret)
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("L'identifiant ne doit contenir que des lettres, chiffres, tirets et underscores"),
            code='invalid_identifier'
        )
    
    return value


def validate_no_special_chars(value):
    """
    Valide qu'une chaîne ne contient pas de caractères spéciaux dangereux
    """
    if not value:
        return value
    
    dangerous = [';', '--', '/*', '*/', '\\x', '%', '`', '$', '|']
    for char in dangerous:
        if char in value:
            raise ValidationError(
                _(f"Caractère non autorisé: {char}"),
                code='dangerous_character'
            )
    
    return value


# ============================================================================
# EMAIL, DOMAINES, URL
# ============================================================================

def validate_email(value):
    """
    Valide une adresse email
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        raise ValidationError(_("Adresse email invalide"), code='invalid_email')
    
    return value


def validate_domain_name(value):
    """
    Valide un nom de domaine
    """
    if not value:
        return value
    
    pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    if not re.match(pattern, value):
        raise ValidationError(_("Nom de domaine invalide"), code='invalid_domain')
    
    return value


def validate_url_safe(value):
    """
    Valide un slug URL-safe
    """
    if not value:
        return value
    
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("Le slug doit contenir des lettres minuscules, chiffres et tirets"),
            code='invalid_slug'
        )
    
    return value


# ============================================================================
# DATES ET FUSEAUX
# ============================================================================

def validate_date_range(start_date, end_date):
    """
    Valide une plage de dates
    """
    if start_date and end_date:
        if start_date > end_date:
            raise ValidationError(
                _("La date de début doit être antérieure à la date de fin"),
                code='invalid_date_range'
            )
    return True


def validate_timezone(value):
    """
    Valide un fuseau horaire
    """
    if not value:
        return value
    
    try:
        import pytz
        pytz.timezone(value)
        return value
    except ImportError:
        # Si pytz n'est pas installé, validation basique
        if value in ['UTC', 'Europe/Paris', 'America/New_York', 'Asia/Tokyo']:
            return value
        raise ValidationError(_("Fuseau horaire invalide"), code='invalid_timezone')
    except pytz.UnknownTimeZoneError:
        raise ValidationError(_("Fuseau horaire inconnu"), code='unknown_timezone')


# ============================================================================
# VALIDATEURS DE MODÈLES
# ============================================================================

def validate_unique_field(model, field_name, value, exclude_id=None):
    """
    Valide l'unicité d'un champ
    """
    if not value:
        return value
    
    kwargs = {field_name: value}
    if exclude_id:
        queryset = model.objects.exclude(id=exclude_id)
    else:
        queryset = model.objects.all()
    
    if queryset.filter(**kwargs).exists():
        raise ValidationError(
            _(f"La valeur '{value}' existe déjà"),
            code='duplicate_value'
        )
    
    return value