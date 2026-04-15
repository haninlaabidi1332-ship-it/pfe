from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import NetworkReport, AlertHistory
from .serializers import NetworkReportSerializer, AlertHistorySerializer

class NetworkReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NetworkReport.objects.all()
    serializer_class = NetworkReportSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['report_type']

class AlertHistoryViewSet(viewsets.ModelViewSet):
    queryset = AlertHistory.objects.all()
    serializer_class = AlertHistorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['olt', 'severity', 'is_resolved']