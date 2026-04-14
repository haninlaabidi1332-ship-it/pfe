from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import SNMPMetric, BFDSession, PerformanceMetric
from .serializers import SNMPMetricSerializer, BFDSessionSerializer, PerformanceMetricSerializer

class SNMPMetricViewSet(viewsets.ModelViewSet):
    queryset = SNMPMetric.objects.all()
    serializer_class = SNMPMetricSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['olt', 'metric_name']

class BFDSessionViewSet(viewsets.ModelViewSet):
    queryset = BFDSession.objects.all()
    serializer_class = BFDSessionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['olt', 'session_state']

class PerformanceMetricViewSet(viewsets.ModelViewSet):
    queryset = PerformanceMetric.objects.all()
    serializer_class = PerformanceMetricSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['olt', 'metric_type']