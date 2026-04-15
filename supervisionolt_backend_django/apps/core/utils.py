# apps/core/utils.py
"""
Utilitaires complets pour la plateforme OLT Supervision
- Génération d'identifiants et tokens
- Formatage de données
- Manipulation de données
- Sécurité et validation
- Cache et performances
- Analyse et agrégations
"""
import uuid
import hashlib
import secrets
import string
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from decimal import Decimal
import re

from django.utils import timezone
from django.core.cache import cache
from django.utils.timesince import timesince

logger = logging.getLogger(__name__)


# ============================================================================
# GÉNÉRATION D'IDENTIFIANTS ET TOKENS
# ============================================================================

def generate_unique_id() -> str:
    """Génère un ID unique (UUID)"""
    return str(uuid.uuid4())


def generate_secure_token(length: int = 32) -> str:
    """Génère un token aléatoire sécurisé"""
    return secrets.token_urlsafe(length)


def generate_readable_code(length: int = 8) -> str:
    """Génère un code alphanumérique lisible (sans caractères ambigus)"""
    alphabet = string.ascii_uppercase + string.digits
    # Enlever les caractères ambigus
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_hash(string: str) -> str:
    """Génère un hash SHA256 d'une chaîne"""
    return hashlib.sha256(string.encode()).hexdigest()


def hash_file(file_obj) -> str:
    """Génère un hash MD5 d'un fichier"""
    hasher = hashlib.md5()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()


# ============================================================================
# FORMATAGE DE DONNÉES
# ============================================================================

def format_bytes(size_bytes: int) -> str:
    """Formate une taille en bytes (humain lisible)"""
    if size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.1f} {units[i]}"


def format_duration(seconds: float) -> str:
    """Formate une durée en secondes (humain lisible)"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def format_timesince(dt, default="maintenant") -> str:
    """Formate le temps écoulé depuis une date"""
    if not dt:
        return default
    return timesince(dt)


def format_number(value: Any, decimals: int = 2, compact: bool = False) -> str:
    """Formate un nombre avec unités K/M/B"""
    if value is None:
        return "N/A"
    
    try:
        num = float(value)
        
        if compact:
            if abs(num) >= 1_000_000_000:
                return f"{num / 1_000_000_000:.{decimals}f}B"
            elif abs(num) >= 1_000_000:
                return f"{num / 1_000_000:.{decimals}f}M"
            elif abs(num) >= 1_000:
                return f"{num / 1_000:.{decimals}f}K"
        
        # Formatage avec séparateurs de milliers
        if isinstance(value, (int, float)) and not compact:
            return f"{num:,.{decimals}f}".replace(",", " ")
        
        return f"{num:.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: float, decimals: int = 1, include_sign: bool = False) -> str:
    """Formate un pourcentage"""
    if value is None:
        return "N/A"
    
    sign = '+' if include_sign and value > 0 else ''
    return f"{sign}{value:.{decimals}f}%"


def format_currency(value: float, currency: str = '€', decimals: int = 2) -> str:
    """Formate une valeur monétaire (utile pour coûts, budgets)"""
    if value is None:
        return "N/A"
    
    formatted = f"{value:,.{decimals}f}".replace(",", " ")
    return f"{formatted} {currency}"


def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Tronque une chaîne à une longueur maximale"""
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# ============================================================================
# MANIPULATION DE DONNÉES
# ============================================================================

def parse_json_field(value: Any, default: Any = None) -> Union[Dict, List]:
    """Parse un champ JSON de manière sécurisée"""
    if not value:
        return default or {}
    
    if isinstance(value, (dict, list)):
        return value
    
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default or {}


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Aplatit un dictionnaire imbriqué"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}{sep}{i}", sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", item))
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Divise une liste en morceaux"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """Division sécurisée (évite la division par zéro)"""
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_percentage_change(old_value: float, new_value: float) -> Optional[float]:
    """Calcule le changement en pourcentage entre deux valeurs"""
    if old_value == 0:
        return None
    return ((new_value - old_value) / abs(old_value)) * 100


def calculate_trend(current: float, previous: float) -> Dict[str, Any]:
    """
    Calcule la tendance entre deux valeurs
    """
    if previous == 0:
        change = 0 if current == 0 else 100
    else:
        change = ((current - previous) / previous) * 100
    
    direction = 'up' if change > 0 else 'down' if change < 0 else 'stable'
    icon = '📈' if change > 0 else '📉' if change < 0 else '➡️'
    
    return {
        'value': current,
        'previous': previous,
        'change': round(change, 1),
        'direction': direction,
        'icon': icon,
        'percentage': format_percentage(change, 1)
    }


def get_client_ip(request) -> str:
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================================
# PLAGES DE DATES
# ============================================================================

def get_date_range(period: str = 'day') -> Tuple[datetime, datetime]:
    """Retourne une plage de dates selon la période"""
    now = timezone.now()
    
    ranges = {
        'day': (now - timedelta(days=1), now),
        'week': (now - timedelta(weeks=1), now),
        'month': (now - timedelta(days=30), now),
        'quarter': (now - timedelta(days=90), now),
        'year': (now - timedelta(days=365), now),
        'today': (now.replace(hour=0, minute=0, second=0, microsecond=0), now),
        'yesterday': (
            (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        'this_week': (
            (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
            now
        ),
        'this_month': (
            now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            now
        ),
        'this_year': (
            now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            now
        ),
    }
    
    return ranges.get(period, ranges['day'])


def get_date_ranges() -> Dict[str, Tuple]:
    """Retourne les plages de dates communes"""
    now = timezone.now()
    today = now.date()
    
    return {
        'today': (today, today),
        'yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
        'last_7_days': (today - timedelta(days=7), today),
        'last_30_days': (today - timedelta(days=30), today),
        'last_90_days': (today - timedelta(days=90), today),
        'this_month': (today.replace(day=1), today),
        'this_year': (today.replace(month=1, day=1), today),
        'last_year': (
            today.replace(year=today.year - 1, month=1, day=1),
            today.replace(year=today.year - 1, month=12, day=31)
        ),
    }


def parse_filter_params(query_params: Dict) -> Dict:
    """Parse les paramètres de filtre communs"""
    filters = {}
    
    # Date range
    date_from = query_params.get('date_from')
    date_to = query_params.get('date_to')
    if date_from:
        filters['created_at__date__gte'] = date_from
    if date_to:
        filters['created_at__date__lte'] = date_to
    
    # Preset ranges
    preset = query_params.get('date_range')
    if preset:
        ranges = get_date_ranges()
        if preset in ranges:
            start, end = ranges[preset]
            filters['created_at__date__gte'] = start
            filters['created_at__date__lte'] = end
    
    return filters


# ============================================================================
# CACHE ET PERFORMANCE
# ============================================================================

def build_cache_key(*args) -> str:
    """Construit une clé de cache cohérente"""
    parts = [str(a) for a in args if a is not None]
    return ':'.join(parts)


def rate_limit_check(key: str, max_calls: int, period_seconds: int) -> bool:
    """
    Limitation de taux simple avec Redis.
    Retourne True si dans les limites, False si dépassé.
    """
    cache_key = f"rate_limit:{key}"
    current = cache.get(cache_key, 0)
    
    if current >= max_calls:
        return False
    
    if current == 0:
        cache.set(cache_key, 1, period_seconds)
    else:
        cache.incr(cache_key)
    
    return True


class Timer:
    """Timer simple pour le monitoring des performances"""
    
    def __init__(self, name: str = 'operation'):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed = 0
    
    def start(self):
        """Démarre le timer"""
        self.start_time = timezone.now()
        return self
    
    def stop(self):
        """Arrête le timer"""
        self.end_time = timezone.now()
        if self.start_time:
            self.elapsed = (self.end_time - self.start_time).total_seconds() * 1000
        return self
    
    def duration(self) -> Optional[float]:
        """Retourne la durée en secondes"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def duration_ms(self) -> Optional[float]:
        """Retourne la durée en millisecondes"""
        seconds = self.duration()
        return seconds * 1000 if seconds else None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
        if self.elapsed > 1000:
            logger.debug(f"{self.name} took {self.elapsed:.2f}ms")


# ============================================================================
# ANALYSE DE DONNÉES (statistiques, agrégations)
# ============================================================================

def calculate_statistics(data: List[Dict], field: str) -> Dict[str, Any]:
    """
    Calcule des statistiques sur une liste de données (min, max, avg, sum, median)
    """
    if not data:
        return {'count': 0, 'sum': 0, 'avg': 0, 'min': 0, 'max': 0}
    
    values = [float(item.get(field, 0)) for item in data if item.get(field) is not None]
    
    if not values:
        return {'count': 0, 'sum': 0, 'avg': 0, 'min': 0, 'max': 0}
    
    return {
        'count': len(values),
        'sum': sum(values),
        'avg': sum(values) / len(values),
        'min': min(values),
        'max': max(values),
        'median': sorted(values)[len(values) // 2],
    }


def safe_eval_expression(expression: str, context: Dict = None) -> Any:
    """
    Évalue une expression de manière sécurisée (pour les formules personnalisées)
    """
    import ast
    import operator as op
    
    operators = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod,
        ast.USub: op.neg,
    }
    
    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if context and node.id in context:
                return context[node.id]
            raise NameError(f"Variable non définie: {node.id}")
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(f"Type non supporté: {type(node)}")
    
    try:
        tree = ast.parse(expression, mode='eval')
        return _eval(tree.body)
    except Exception as e:
        logger.error(f"Erreur évaluation expression: {e}")
        return None


# ============================================================================
# VALIDATION ET SÉCURITÉ
# ============================================================================

def validate_email(email: str) -> bool:
    """Valide une adresse email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_ip_address(ip: str) -> bool:
    """Valide une adresse IPv4 ou IPv6"""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_snmp_community(community: str) -> bool:
    """Validation basique pour une communauté SNMP (non vide, pas de caractères spéciaux dangereux)"""
    if not community:
        return False
    # Empêcher les caractères de contrôle ou les espaces
    if any(c in community for c in ['\n', '\r', '\t', ' ']):
        return False
    return True