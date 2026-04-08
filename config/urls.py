"""
IOTShield Platform URLs - Ultra Professional
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# drf-yasg schema
schema_view_yasg = get_schema_view(
    openapi.Info(
        title="Sotifibre BI Platform API",
        default_version='v1',
        description="Plateforme d'analyse de données et Business Intelligence avancée.",
        contact=openapi.Contact(email="sotifibre@sotetel.tn"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),

    # ========================================================================
    # CORE APPLICATIONS
    # ========================================================================
    
    # Users App - Gestion des utilisateurs OLT Supervision
    path('api/users/', include('apps.users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass