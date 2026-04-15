from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# CRUCIAL : On donne des noms de chemin différents pour chaque ViewSet
router.register('accounts', views.UserViewSet, basename='user') # Devient /api/users/accounts/
router.register('teams', views.TeamViewSet, basename='team')       # Devient /api/users/teams/
router.register('roles', views.RoleViewSet, basename='role')       # Devient /api/users/roles/
router.register('permissions', views.PermissionViewSet, basename='permission')
router.register('activities', views.UserActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
]