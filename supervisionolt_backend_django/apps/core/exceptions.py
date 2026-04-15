# apps/core/exceptions.py
"""
Gestionnaire d'exceptions personnalisé pour la plateforme OLT Supervision 
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour DIGI STOCK
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "status": False,
            "message": "Une erreur est survenue.",
            "errors": {},
        }

        if hasattr(response, "data"):
            data = response.data
            if isinstance(data, dict):
                if "detail" in data:
                    error_data["message"] = str(data["detail"])
                elif "message" in data:
                    error_data["message"] = str(data["message"])
                else:
                    error_data["errors"] = data
                    error_data["message"] = "Erreur de validation."
            elif isinstance(data, list):
                error_data["errors"] = {"non_field_errors": data}
                error_data["message"] = str(data[0]) if data else "Erreur."

        status_code = response.status_code
        if status_code == 400:
            error_data["code"] = "bad_request"
        elif status_code == 401:
            error_data["code"] = "unauthorized"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Non authentifié."
        elif status_code == 403:
            error_data["code"] = "forbidden"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Permission refusée."
        elif status_code == 404:
            error_data["code"] = "not_found"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Ressource non trouvée."
        elif status_code == 405:
            error_data["code"] = "method_not_allowed"
            error_data["message"] = "Méthode non autorisée."
        elif status_code == 409:
            error_data["code"] = "conflict"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Conflit de ressource."
        elif status_code == 422:
            error_data["code"] = "validation_error"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Erreur de validation."
        elif status_code == 429:
            error_data["code"] = "too_many_requests"
            error_data["message"] = "Trop de requêtes. Veuillez réessayer plus tard."
        elif status_code >= 500:
            error_data["code"] = "server_error"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Erreur interne du serveur."

        response.data = error_data
        
    else:
        logger.exception("Exception non gérée: %s", exc)
        
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "Erreur interne du serveur."
        code = "server_error"
        
        if isinstance(exc, Http404):
            status_code = status.HTTP_404_NOT_FOUND
            message = "Ressource non trouvée."
            code = "not_found"
        elif isinstance(exc, PermissionDenied):
            status_code = status.HTTP_403_FORBIDDEN
            message = "Permission refusée."
            code = "forbidden"
        elif isinstance(exc, ValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Erreur de validation."
            code = "validation_error"
            error_data = {
                "status": False,
                "message": message,
                "errors": exc.message_dict if hasattr(exc, 'message_dict') else exc.messages,
                "code": code,
            }
            from django.utils import timezone
            error_data["timestamp"] = timezone.now().isoformat()
            return Response(error_data, status=status_code)
        
        response = Response(
            {
                "status": False,
                "message": message,
                "errors": {},
                "code": code,
            },
            status=status_code,
        )
        
        from django.utils import timezone
        response.data["timestamp"] = timezone.now().isoformat()

    return response


# ========================================================================
# EXCEPTIONS SPÉCIFIQUES À LA SUPERVISION OLT
# ========================================================================

class OLTException(Exception):
    """Exception de base pour la plateforme OLT Supervision"""
    
    def __init__(self, message="Une erreur OLT est survenue", code=None, status_code=400):
        self.message = message
        self.code = code or "olt_error"
        self.status_code = status_code
        super().__init__(self.message)


class OLTNotFoundException(OLTException):
    """Exception pour OLT non trouvé"""
    
    def __init__(self, olt_id=None, message=None):
        if not message:
            message = f"Équipement OLT non trouvé" + (f" : {olt_id}" if olt_id else "")
        super().__init__(message, code="olt_not_found", status_code=404)


class SNMPConnectionException(OLTException):
    """Exception pour échec de connexion SNMP"""
    
    def __init__(self, olt_name=None, reason=None, message=None):
        if not message:
            message = f"Échec de connexion SNMP" + (f" à {olt_name}" if olt_name else "") + (f" : {reason}" if reason else "")
        super().__init__(message, code="snmp_connection_failed", status_code=500)


class BFDException(OLTException):
    """Exception pour erreur BFD"""
    
    def __init__(self, olt_name=None, message=None):
        if not message:
            message = f"Erreur BFD" + (f" sur {olt_name}" if olt_name else "")
        super().__init__(message, code="bfd_error", status_code=500)


class MetricCollectionException(OLTException):
    """Exception pour erreur de collecte des métriques"""
    
    def __init__(self, olt_name=None, metric_type=None, message=None):
        if not message:
            message = f"Erreur de collecte" + (f" de {metric_type}" if metric_type else "") + (f" sur {olt_name}" if olt_name else "")
        super().__init__(message, code="metric_collection_error", status_code=500)


class AnomalyDetectionException(OLTException):
    """Exception pour erreur lors de la détection d'anomalies"""
    
    def __init__(self, message=None):
        if not message:
            message = "Erreur lors de la détection d'anomalies"
        super().__init__(message, code="anomaly_detection_error", status_code=500)


class AlertGenerationException(OLTException):
    """Exception pour erreur lors de la génération d'alerte"""
    
    def __init__(self, message=None):
        if not message:
            message = "Erreur lors de la génération d'alerte"
        super().__init__(message, code="alert_generation_error", status_code=500)


class InvalidSNMPCommunityException(OLTException):
    """Exception pour communauté SNMP invalide"""
    
    def __init__(self, community=None, message=None):
        if not message:
            message = f"Communauté SNMP invalide" + (f" : {community}" if community else "")
        super().__init__(message, code="invalid_snmp_community", status_code=400)


class OLTConfigurationException(OLTException):
    """Exception pour erreur de configuration OLT"""
    
    def __init__(self, olt_name=None, message=None):
        if not message:
            message = f"Erreur de configuration OLT" + (f" pour {olt_name}" if olt_name else "")
        super().__init__(message, code="olt_configuration_error", status_code=400)