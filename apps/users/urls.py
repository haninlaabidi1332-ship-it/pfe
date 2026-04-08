# apps/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('users', views.UserViewSet)
router.register('teams', views.TeamViewSet)
router.register('roles', views.RoleViewSet)
router.register('permissions', views.PermissionViewSet)
router.register('activities', views.UserActivityViewSet)

urlpatterns = router.urls