from django.urls import path
from .views import GlobalStatsView

urlpatterns = [
    path('global-stats/', GlobalStatsView.as_view(), name='global-stats'),
]