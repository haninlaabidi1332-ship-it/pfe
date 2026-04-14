from rest_framework import serializers
from .models import Device, ONU, Interface, Site
from apps.users.serializers import UserMinimalSerializer

# ----------------------------------------------------------------------
# 1. MINIMAL SERIALIZERS (For fast-loading tables)
# ----------------------------------------------------------------------

class DeviceMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for OLT list views"""
    status_icon = serializers.SerializerMethodField()
    is_reachable = serializers.BooleanField(read_only=True)
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'name', 'hostname', 'management_ip', 
            'status', 'status_icon', 'is_reachable', 'site_name'
        ]

    def get_status_icon(self, obj):
        icons = {
            'active': '🟢',
            'inactive': '⏸️',
            'maintenance': '🔧',
            'degraded': '🟡',
            'failed': '🔴',
        }
        return icons.get(obj.status, '⚪')

# ----------------------------------------------------------------------
# 2. INTERFACE SERIALIZER (C'EST CELUI QUI MANQUAIT !)
# ----------------------------------------------------------------------

class InterfaceSerializer(serializers.ModelSerializer):
    """Serializer pour les ports OLT (Interfaces)"""
    class Meta:
        model = Interface
        fields = '__all__'

# ----------------------------------------------------------------------
# 3. DETAILED SERIALIZERS (For individual pages)
# ----------------------------------------------------------------------

class ONUDetailedSerializer(serializers.ModelSerializer):
    """Detailed view for a specific ONU"""
    status_badge = serializers.SerializerMethodField()
    optical_health = serializers.SerializerMethodField()

    class Meta:
        model = ONU
        fields = '__all__'

    def get_status_badge(self, obj):
        badges = {'active': '✅ Active', 'offline': '❌ Offline', 'failed': '⚠️ Alarm'}
        return badges.get(obj.status, obj.status)

    def get_optical_health(self, obj):
        if obj.rx_power_dbm is None: return "Unknown"
        if -27.0 <= obj.rx_power_dbm <= -8.0:
            return "Good"
        return "Critical"

class DeviceDetailSerializer(serializers.ModelSerializer):
    """Complete detail of an OLT including its ports and owner"""
    interfaces = InterfaceSerializer(many=True, read_only=True)
    owner_details = UserMinimalSerializer(source='owner', read_only=True)
    uptime_display = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()


    class Meta:
        model = Device
        exclude = ['password', 'snmp_community'] # Sécurité
        read_only_fields = ['last_seen', 'cpu_usage', 'memory_usage']

    def get_uptime_display(self, obj):
        uptime = getattr(obj, 'uptime_seconds', 0)
        if not uptime: return "N/A"
        days = uptime // 86400
        return f"{days} days"

    def get_can_edit(self, obj):
        # Correction ici pour éviter le crash si on n'est pas connecté
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.is_staff or getattr(request.user, 'can_manage_olts', False)
        return False

# ----------------------------------------------------------------------
# 4. STATS SERIALIZERS (For Dashboards)
# ----------------------------------------------------------------------

class InventoryStatsSerializer(serializers.Serializer):
    total_olts = serializers.IntegerField()
    total_onus = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    status_distribution = serializers.DictField()
    network_utilization = serializers.FloatField()