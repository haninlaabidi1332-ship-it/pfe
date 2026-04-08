# apps/core/responses.py
"""
Réponses standardisées pour la plateforme OLT Supervision
"""
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone


def success_response(data=None, message="Succès", status_code=status.HTTP_200_OK, meta=None):
    """Réponse de succès standard avec métadonnées optionnelles"""
    response_data = {
        "status": True,
        "message": message,
        "data": data,
        "timestamp": timezone.now().isoformat(),
    }
    
    if meta:
        response_data["meta"] = meta
    
    return Response(response_data, status=status_code)


def created_response(data=None, message="Créé avec succès", meta=None):
    """Réponse 201 Créé"""
    return success_response(data, message, status.HTTP_201_CREATED, meta)


def error_response(message="Une erreur est survenue", errors=None, status_code=status.HTTP_400_BAD_REQUEST, code=None):
    """Réponse d'erreur standard"""
    response_data = {
        "status": False,
        "message": message,
        "timestamp": timezone.now().isoformat(),
    }
    
    if errors:
        response_data["errors"] = errors
    
    if code:
        response_data["code"] = code
    
    return Response(response_data, status=status_code)


def not_found_response(message="Ressource non trouvée", resource_type=None, resource_id=None):
    """Réponse 404 Non trouvé"""
    errors = {}
    if resource_type and resource_id:
        errors = {resource_type: f"{resource_id} non trouvé(e)"}
    
    return error_response(
        message=message,
        errors=errors,
        status_code=status.HTTP_404_NOT_FOUND,
        code="not_found"
    )


def forbidden_response(message="Permission refusée", required_permission=None):
    """Réponse 403 Interdit"""
    errors = {}
    if required_permission:
        errors["required"] = required_permission
    
    return error_response(
        message=message,
        errors=errors,
        status_code=status.HTTP_403_FORBIDDEN,
        code="forbidden"
    )


def validation_error_response(errors, message="Erreur de validation"):
    """Réponse 422 Erreur de validation"""
    return error_response(
        message=message,
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="validation_error"
    )


def conflict_response(message="Conflit de ressource", details=None):
    """Réponse 409 Conflit"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_409_CONFLICT,
        code="conflict"
    )


def unauthorized_response(message="Non authentifié", details=None):
    """Réponse 401 Non autorisé"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="unauthorized"
    )


def bad_request_response(message="Requête invalide", details=None):
    """Réponse 400 Mauvaise requête"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_400_BAD_REQUEST,
        code="bad_request"
    )


def server_error_response(message="Erreur interne du serveur", details=None):
    """Réponse 500 Erreur serveur"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="server_error"
    )


def service_unavailable_response(message="Service temporairement indisponible", details=None):
    """Réponse 503 Service indisponible"""
    return error_response(
        message=message,
        errors=details,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="service_unavailable"
    )


# ========================================================================
# RÉPONSES SPÉCIFIQUES À LA SUPERVISION OLT
# ========================================================================

def metrics_response(metrics_data, olt_name=None):
    """Réponse pour les métriques d'un OLT"""
    response_data = {
        "olt": olt_name,
        "metrics": metrics_data,
        "timestamp": timezone.now().isoformat(),
    }
    return success_response(response_data, "Métriques récupérées")


def alert_response(alerts, count=None):
    """Réponse pour les alertes"""
    response_data = {
        "alerts": alerts,
        "count": count or len(alerts),
        "timestamp": timezone.now().isoformat(),
    }
    return success_response(response_data, "Alertes récupérées")


def anomaly_response(anomalies, olt_name=None):
    """Réponse pour les anomalies détectées"""
    response_data = {
        "olt": olt_name,
        "anomalies": anomalies,
        "timestamp": timezone.now().isoformat(),
    }
    return success_response(response_data, "Anomalies détectées")