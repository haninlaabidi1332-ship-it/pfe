# apps/core/pagination.py
"""
Pagination personnalisée pour la plateforme OLT Supervision
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """Pagination standard pour OLT Supervision"""
    page_size = 20
    page_size_query_param = "per_page"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": True,
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
            "_meta": {
                "page_size": self.page_size,
                "page_size_query_param": self.page_size_query_param,
                "max_page_size": self.max_page_size,
            }
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "status": {"type": "boolean"},
                "count": {"type": "integer"},
                "total_pages": {"type": "integer"},
                "current_page": {"type": "integer"},
                "next": {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "results": schema,
                "_meta": {
                    "type": "object",
                    "properties": {
                        "page_size": {"type": "integer"},
                        "page_size_query_param": {"type": "string"},
                        "max_page_size": {"type": "integer"},
                    }
                }
            },
        }


class LargeResultsPagination(PageNumberPagination):
    """Pagination pour les grands jeux de données (ex: historique des métriques)"""
    page_size = 100
    page_size_query_param = "per_page"
    max_page_size = 1000


class DashboardPagination(PageNumberPagination):
    """Pagination pour les tableaux de bord (si utilisé)"""
    page_size = 10
    page_size_query_param = "per_page"
    max_page_size = 50