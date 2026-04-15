from rest_framework import viewsets
from .models import AlertPolicy, ActiveAlert, NotificationChannel
from .serializers import AlertPolicySerializer, ActiveAlertSerializer, NotificationChannelSerializer

class AlertPolicyViewSet(viewsets.ModelViewSet):
    queryset = AlertPolicy.objects.all()
    serializer_class = AlertPolicySerializer

class ActiveAlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActiveAlert.objects.all()
    serializer_class = ActiveAlertSerializer

class NotificationChannelViewSet(viewsets.ModelViewSet):
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer