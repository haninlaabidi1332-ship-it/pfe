# apps/core/middleware.py
"""
Middlewares pour la plateforme OLT Supervision
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("request")


class RequestLoggingMiddleware:
    """Log all incoming requests with duration."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = (time.time() - start) * 1000
        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.path,
            response.status_code,
            duration,
        )
        return response


class QueryPerformanceMiddleware(MiddlewareMixin):
    """
    Middleware pour monitorer les performances des requêtes
    """
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000
            
            # Log des requêtes lentes
            if duration > 1000:  # Plus d'1 seconde
                logger.warning(
                    f"Requête lente: {request.method} {request.path} - {duration:.2f}ms"
                )
            
            # Ajouter le temps d'exécution dans les headers
            response['X-Query-Time-Ms'] = int(duration)
        
        return response


class APIRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware pour la limitation de débit API
    (À implémenter avec Redis si nécessaire)
    """
    
    def process_request(self, request):
        # Placeholder pour une future implémentation
        pass


class OLTResponseMiddleware(MiddlewareMixin):
    """
    Middleware pour enrichir les réponses JSON avec des métadonnées
    """
    
    def process_response(self, request, response):
        if response.status_code == 200 and response.get('Content-Type') == 'application/json':
            try:
                data = json.loads(response.content)
                if isinstance(data, dict):
                    data['_meta'] = {
                        'timestamp': time.time(),
                        'platform': 'OLT Supervision',
                        'version': '1.0.0'
                    }
                    response.content = json.dumps(data)
            except Exception:
                pass
        return response