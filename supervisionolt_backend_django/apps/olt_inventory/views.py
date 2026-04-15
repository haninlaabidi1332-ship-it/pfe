# Create your views here.
# apps/olt_inventory/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Device, ONU, Interface
from .serializers import (
    DeviceMinimalSerializer, 
    DeviceDetailSerializer,
    ONUDetailedSerializer,
    InterfaceSerializer
)

class DeviceViewSet(viewsets.ModelViewSet):
    """
    Viewset pour la gestion des OLTs avec switch dynamique de sérialiseur.
    """
    queryset = Device.objects.all().select_related('site', 'owner')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'site', 'device_type']
    search_fields = ['name', 'hostname', 'management_ip', 'serial_number']
    ordering_fields = ['created_at', 'last_seen', 'cpu_usage']

    def get_serializer_class(self):
        """
        Retourne le sérialiseur Minimal pour la liste 
        et le sérialiseur Detail pour voir un OLT spécifique.
        """
        if self.action == 'list':
            return DeviceMinimalSerializer
        return DeviceDetailSerializer

    @action(detail=True, methods=['get'])
    def interfaces(self, request, pk=None):
        """Endpoint personnalisé: /api/devices/{id}/interfaces/"""
        device = self.get_object()
        interfaces = device.interfaces.all()
        serializer = InterfaceSerializer(interfaces, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reboot(self, request, pk=None):
        """Action personnalisée pour redémarrer un OLT"""
        device = self.get_object()
        # Ici vous ajouteriez votre logique SSH/SNMP
        return Response({'status': f'Reboot command sent to {device.name}'})


class ONUViewSet(viewsets.ModelViewSet):
    """
    Viewset pour la supervision des ONUs (Clients).
    """
    queryset = ONU.objects.all().select_related('pon_port__device')
    serializer_class = ONUDetailedSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'pon_port']
    search_fields = ['serial_number', 'customer_name', 'onu_id']

    @action(detail=False, methods=['get'])
    def critical_signals(self, request):
        """Retourne uniquement les ONUs avec un signal faible"""
        critical_onus = self.queryset.filter(rx_power_dbm__lt=-27.0)
        serializer = self.get_serializer(critical_onus, many=True)
        return Response(serializer.data)


class InterfaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vue en lecture seule pour les ports OLT.
    """
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    filterset_fields = ['device', 'status', 'interface_type']