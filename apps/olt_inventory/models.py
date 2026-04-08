# apps/olt_inventory/models.py
"""
Inventory models for OLT Supervision Platform.
Complete network inventory: sites, racks, devices, interfaces, cabling,
power, IPAM, VLANs, circuits, BGP, virtualization, tenancy, L2VPN, PON/ONU.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from apps.core.models import BaseModel, SoftDeleteModel
from apps.users.models import User
import ipaddress
import uuid

# ----------------------------------------------------------------------
# 1. Geographic hierarchy
# ----------------------------------------------------------------------

class Region(BaseModel):
    """Geographic region (e.g., Europe, North America)"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_regions'
        ordering = ['name']
        verbose_name = "Region"
        verbose_name_plural = "Regions"

    def __str__(self):
        return self.name


class Site(BaseModel):
    """Physical site / location"""
    SITE_TYPE_CHOICES = [
        ('datacenter', 'Data Center'),
        ('campus', 'Campus'),
        ('headquarters', 'Headquarters'),
        ('branch', 'Branch Office'),
        ('remote', 'Remote Office'),
        ('pop', 'Point of Presence'),
        ('warehouse', 'Warehouse'),
        ('lab', 'Laboratory'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('planned', 'Planned'),
        ('decommissioned', 'Decommissioned'),
    ]

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    site_type = models.CharField(max_length=50, choices=SITE_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, null=True, blank=True, related_name='sites')
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    contact_name = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_sites'
        ordering = ['name']
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['site_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Location(BaseModel):
    """Location inside a site (room, floor, cage)"""
    LOCATION_TYPE_CHOICES = [
        ('room', 'Room'),
        ('floor', 'Floor'),
        ('suite', 'Suite'),
        ('cage', 'Cage'),
        ('cabinet', 'Cabinet'),
        ('aisle', 'Aisle'),
    ]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=50, choices=LOCATION_TYPE_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    length_m = models.FloatField(null=True, blank=True)
    width_m = models.FloatField(null=True, blank=True)
    height_m = models.FloatField(null=True, blank=True)
    floor_number = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_locations'
        ordering = ['site', 'name']
        unique_together = ['site', 'name']
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return f"{self.site.code} - {self.name}"


# ----------------------------------------------------------------------
# 2. Racks
# ----------------------------------------------------------------------

class Rack(BaseModel):
    """Equipment rack"""
    RACK_TYPE_CHOICES = [
        ('server', 'Server Rack'),
        ('network', 'Network Rack'),
        ('enclosure', 'Enclosure'),
        ('wall_mount', 'Wall Mount'),
    ]
    WIDTH_CHOICES = [('19', '19 inches'), ('23', '23 inches')]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('planned', 'Planned'),
        ('decommissioned', 'Decommissioned'),
    ]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='racks')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='racks')
    name = models.CharField(max_length=100)
    rack_type = models.CharField(max_length=50, choices=RACK_TYPE_CHOICES, default='server')
    width = models.CharField(max_length=10, choices=WIDTH_CHOICES, default='19')
    height_u = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(60)])
    row = models.CharField(max_length=10, blank=True)
    position = models.IntegerField(null=True, blank=True)
    max_power_kw = models.FloatField(null=True, blank=True)
    max_weight_kg = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_racks'
        ordering = ['site', 'name']
        unique_together = ['site', 'name']
        verbose_name = "Rack"
        verbose_name_plural = "Racks"

    def __str__(self):
        return f"{self.site.code} - {self.name}"

    @property
    def device_count(self):
        return self.devices.count()

    @property
    def used_units(self):
        devices = self.devices.filter(rack_position__isnull=False)
        units = []
        for device in devices:
            if device.rack_position and device.device_type.u_height:
                for u in range(device.rack_position, device.rack_position + device.device_type.u_height):
                    units.append(u)
        return units

    @property
    def available_units(self):
        return [u for u in range(1, self.height_u + 1) if u not in self.used_units]


# ----------------------------------------------------------------------
# 3. Manufacturers, Device Types, Roles, Platforms
# ----------------------------------------------------------------------

class Manufacturer(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    support_url = models.URLField(blank=True)
    support_phone = models.CharField(max_length=50, blank=True)
    support_email = models.EmailField(blank=True)

    class Meta:
        db_table = 'inventory_manufacturers'
        ordering = ['name']

    def __str__(self):
        return self.name


class DeviceType(BaseModel):
    """Device model / type"""
    DEVICE_CLASS_CHOICES = [
        ('router', 'Router'),
        ('switch', 'Switch'),
        ('firewall', 'Firewall'),
        ('load_balancer', 'Load Balancer'),
        ('olt', 'OLT'),
        ('onu', 'ONU/ONT'),
        ('server', 'Server'),
        ('storage', 'Storage'),
        ('wireless', 'Wireless Controller/AP'),
        ('management', 'Management'),
        ('other', 'Other'),
    ]

    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name='device_types')
    model = models.CharField(max_length=100)
    device_class = models.CharField(max_length=50, choices=DEVICE_CLASS_CHOICES)
    part_number = models.CharField(max_length=100, blank=True)
    u_height = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(50)])
    power_consumption_w = models.IntegerField(null=True, blank=True)
    interface_count = models.IntegerField(default=0)
    port_count = models.IntegerField(default=0)
    max_throughput_gbps = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_device_types'
        unique_together = ['manufacturer', 'model']
        ordering = ['manufacturer', 'model']

    def __str__(self):
        return f"{self.manufacturer.name} {self.model}"


class DeviceRole(BaseModel):
    """Functional role (core, distribution, access, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    color = models.CharField(max_length=20, default='primary')
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_device_roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class Platform(BaseModel):
    """Network OS platform for automation (IOS, NX-OS, EOS, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    napalm_driver = models.CharField(max_length=100, blank=True)
    netmiko_device_type = models.CharField(max_length=100, blank=True)
    scrapli_driver = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_platforms'
        ordering = ['name']

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------
# 4. Device (core network equipment)
# ----------------------------------------------------------------------

class Device(SoftDeleteModel):
    """Network device (router, switch, OLT, server, etc.)"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
        ('degraded', 'Degraded'),
        ('failed', 'Failed'),
        ('planned', 'Planned'),
        ('staged', 'Staged'),
        ('decommissioned', 'Decommissioned'),
    ]

    # Identification
    name = models.CharField(max_length=100, db_index=True)
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    device_type = models.ForeignKey(DeviceType, on_delete=models.PROTECT, related_name='devices')
    device_class = models.CharField(
        max_length=50,
        choices=DeviceType.DEVICE_CLASS_CHOICES,
        blank=True,
        help_text="Classe dénormalisée pour faciliter les filtres (synchro automatique)"
    )
    device_role = models.ForeignKey(DeviceRole, on_delete=models.PROTECT, null=True, blank=True, related_name='devices')
    platform = models.ForeignKey(Platform, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')

    # Location
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name='devices')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    rack = models.ForeignKey(Rack, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    rack_position = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    face = models.CharField(max_length=10, choices=[('front', 'Front'), ('rear', 'Rear')], default='front')

    # Management
    management_ip = models.GenericIPAddressField(db_index=True)
    serial_number = models.CharField(max_length=100, blank=True, db_index=True)
    asset_tag = models.CharField(max_length=100, blank=True)

    # SNMP / credentials
    snmp_community = models.CharField(max_length=100, blank=True)
    snmp_version = models.CharField(max_length=10, default='2c')
    snmp_port = models.IntegerField(default=161)
    snmp_timeout = models.FloatField(default=5.0)
    snmp_retries = models.IntegerField(default=2)

    username = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=255, blank=True)  # to be encrypted
    ssh_port = models.IntegerField(default=22)
    enable_password = models.CharField(max_length=255, blank=True)

    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active', db_index=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    uptime_seconds = models.BigIntegerField(null=True, blank=True)

    # Hardware
    firmware_version = models.CharField(max_length=100, blank=True)
    hardware_version = models.CharField(max_length=100, blank=True)

    # Metrics (cached from monitoring)
    cpu_usage = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    memory_usage = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    temperature = models.FloatField(null=True, blank=True)

    # Ownership & metadata
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_devices')
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    objects = models.Manager()  # default manager (including soft-deleted)

    class Meta:
        db_table = 'inventory_devices'
        ordering = ['site', 'name']
        verbose_name = "Device"
        verbose_name_plural = "Devices"
        indexes = [
            models.Index(fields=['hostname']),
            models.Index(fields=['status']),
            models.Index(fields=['device_type']),
            models.Index(fields=['site', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.hostname})"

    @property
    def is_reachable(self):
        if self.last_seen:
            delta = timezone.now() - self.last_seen
            return delta.total_seconds() < 600
        return False

    @property
    def interface_count(self):
        return self.interfaces.filter(is_deleted=False).count()

    def save(self, *args, **kwargs):
        """Override save to synchronize device_class from device_type"""
        if self.device_type:
            self.device_class = self.device_type.device_class
        super().save(*args, **kwargs)


# ----------------------------------------------------------------------
# 5. Interfaces, Cables, Power
# ----------------------------------------------------------------------

class Interface(SoftDeleteModel):
    """Network interface (physical or logical)"""
    INTERFACE_TYPE_CHOICES = [
        ('ethernet', 'Ethernet'),
        ('fastethernet', 'FastEthernet'),
        ('gigabitethernet', 'GigabitEthernet'),
        ('tengigabitethernet', '10GE'),
        ('fortygigabitethernet', '40GE'),
        ('hundredgigabitethernet', '100GE'),
        ('pon', 'PON (GPON/XGS-PON)'),
        ('xgs_pon', 'XGS-PON'),
        ('epon', 'EPON'),
        ('loopback', 'Loopback'),
        ('vlan', 'VLAN Interface'),
        ('port_channel', 'Port Channel'),
        ('management', 'Management'),
        ('console', 'Console'),
    ]
    STATUS_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('testing', 'Testing'),
        ('disabled', 'Disabled'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='interfaces')
    name = models.CharField(max_length=100)
    interface_type = models.CharField(max_length=50, choices=INTERFACE_TYPE_CHOICES)
    enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='down')
    mac_address = models.CharField(max_length=17, blank=True)
    mtu = models.IntegerField(default=1500, validators=[MinValueValidator(68), MaxValueValidator(9216)])
    speed_mbps = models.IntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)

    # PON specific
    pon_type = models.CharField(max_length=20, choices=[('gpon','GPON'),('xgspon','XGS-PON'),('combo','Combo'),('epon','EPON')], null=True, blank=True)
    pon_port_index = models.CharField(max_length=50, blank=True)  # e.g., "1/1/1"

    # Statistics (updated by monitoring)
    rx_bytes = models.BigIntegerField(default=0)
    tx_bytes = models.BigIntegerField(default=0)
    rx_packets = models.BigIntegerField(default=0)
    tx_packets = models.BigIntegerField(default=0)
    rx_errors = models.BigIntegerField(default=0)
    tx_errors = models.BigIntegerField(default=0)
    rx_drops = models.BigIntegerField(default=0)
    tx_drops = models.BigIntegerField(default=0)

    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_interfaces'
        unique_together = ['device', 'name']
        ordering = ['device', 'name']
        indexes = [
            models.Index(fields=['device', 'status']),
            models.Index(fields=['mac_address']),
        ]

    def __str__(self):
        return f"{self.device.name}:{self.name}"


class Cable(SoftDeleteModel):
    """Physical cable between two interfaces"""
    CABLE_TYPE_CHOICES = [
        ('cat5e', 'Cat5e'), ('cat6', 'Cat6'), ('cat6a', 'Cat6a'),
        ('cat7', 'Cat7'), ('cat8', 'Cat8'),
        ('mmf', 'Multimode Fiber'), ('smf', 'Singlemode Fiber'),
        ('dac', 'DAC'), ('coax', 'Coaxial'), ('power', 'Power'),
    ]
    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('planned', 'Planned'),
        ('decommissioned', 'Decommissioned'),
    ]

    cable_type = models.CharField(max_length=50, choices=CABLE_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='connected')
    interface_a = models.ForeignKey(Interface, on_delete=models.PROTECT, related_name='cables_a')
    interface_b = models.ForeignKey(Interface, on_delete=models.PROTECT, related_name='cables_b')
    length_m = models.FloatField(null=True, blank=True)
    color = models.CharField(max_length=50, blank=True)
    label = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_cables'
        unique_together = ['interface_a', 'interface_b']
        verbose_name = "Cable"
        verbose_name_plural = "Cables"

    def __str__(self):
        return f"{self.interface_a} ↔ {self.interface_b}"


class PowerPort(SoftDeleteModel):
    """Power port on a device"""
    PORT_TYPE_CHOICES = [
        ('iec_c13', 'IEC C13'), ('iec_c19', 'IEC C19'),
        ('nema_5_15', 'NEMA 5-15'), ('nema_5_20', 'NEMA 5-20'),
        ('dc_terminal', 'DC Terminal'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='power_ports')
    name = models.CharField(max_length=100)
    port_type = models.CharField(max_length=50, choices=PORT_TYPE_CHOICES)
    allocated_power_w = models.IntegerField(default=0)
    max_power_w = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_power_ports'
        unique_together = ['device', 'name']
        ordering = ['device', 'name']

    def __str__(self):
        return f"{self.device.name}:{self.name}"


class PowerFeed(SoftDeleteModel):
    """Power feed from PDU/UPS to a power port"""
    power_port = models.ForeignKey(PowerPort, on_delete=models.CASCADE, related_name='feeds')
    source = models.CharField(max_length=100)
    voltage_v = models.FloatField(null=True, blank=True)
    amperage_a = models.FloatField(null=True, blank=True)
    power_w = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_measured = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'inventory_power_feeds'
        verbose_name = "Power Feed"
        verbose_name_plural = "Power Feeds"

    def __str__(self):
        return f"{self.power_port} ← {self.source}"


# ----------------------------------------------------------------------
# 6. PON specific models (OLT and ONU)
# ----------------------------------------------------------------------

class OLT(Device):
    """Proxy model for OLT devices (specialized)"""
    class Meta:
        proxy = True
        verbose_name = "OLT Device"
        verbose_name_plural = "OLT Devices"

    @property
    def pon_ports(self):
        return self.interfaces.filter(interface_type__in=['pon', 'xgs_pon', 'epon'])

    @property
    def onu_count(self):
        return ONU.objects.filter(pon_port__device=self, is_deleted=False).count()


class ONU(SoftDeleteModel):
    """Optical Network Unit (customer premises)"""
    ONU_TYPE_CHOICES = [
        ('sfu', 'SFU (Single Family Unit)'),
        ('mtu', 'MTU (Multi Tenant Unit)'),
        ('mdu', 'MDU (Multi Dwelling Unit)'),
        ('business', 'Business ONT'),
        ('wifi', 'Wi-Fi ONT'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('offline', 'Offline'),
        ('configuring', 'Configuring'),
        ('failed', 'Failed'),
        ('deregistered', 'Deregistered'),
    ]

    serial_number = models.CharField(max_length=20, unique=True, db_index=True)
    pon_port = models.ForeignKey(Interface, on_delete=models.CASCADE, related_name='onus', limit_choices_to={'interface_type__in': ['pon', 'xgs_pon', 'epon']})
    onu_id = models.IntegerField(null=True, blank=True, help_text="ID assigned by OLT")
    onu_type = models.CharField(max_length=20, choices=ONU_TYPE_CHOICES, default='sfu')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')

    # Subscriber info
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # Optical metrics
    rx_power_dbm = models.FloatField(null=True, blank=True)
    tx_power_dbm = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    voltage_v = models.FloatField(null=True, blank=True)

    # Service details
    service_profile = models.CharField(max_length=100, blank=True)
    line_rate_down_mbps = models.IntegerField(null=True, blank=True)
    line_rate_up_mbps = models.IntegerField(null=True, blank=True)

    last_seen = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_onus'
        ordering = ['pon_port', 'onu_id']
        indexes = [
            models.Index(fields=['serial_number']),
            models.Index(fields=['status']),
        ]
        verbose_name = "ONU"
        verbose_name_plural = "ONUs"

    def __str__(self):
        return f"ONU {self.serial_number} (ID {self.onu_id})"

    @property
    def olt(self):
        return self.pon_port.device


# ----------------------------------------------------------------------
# 7. IP Address Management (VRF, Prefix, IP Address)
# ----------------------------------------------------------------------

class VRF(BaseModel):
    """Virtual Routing and Forwarding instance"""
    name = models.CharField(max_length=100)
    rd = models.CharField(max_length=100, unique=True, help_text="Route Distinguisher (ASN:NN or IP:NN)")
    description = models.TextField(blank=True)
    enforce_unique = models.BooleanField(default=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='vrfs')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_vrfs'
        ordering = ['name']
        unique_together = ['name', 'rd']
        verbose_name = "VRF"
        verbose_name_plural = "VRFs"

    def __str__(self):
        return f"{self.name} ({self.rd})"

    @property
    def prefix_count(self):
        return self.prefixes.count()

    @property
    def ip_count(self):
        return self.ip_addresses.count()


class Prefix(BaseModel):
    """IP prefix for IPAM"""
    FAMILY_CHOICES = [(4, 'IPv4'), (6, 'IPv6')]
    STATUS_CHOICES = [
        ('container', 'Container'),
        ('active', 'Active'),
        ('reserved', 'Reserved'),
        ('deprecated', 'Deprecated'),
    ]

    prefix = models.CharField(max_length=100, unique=True)
    vrf = models.ForeignKey(VRF, on_delete=models.PROTECT, null=True, blank=True, related_name='prefixes')
    site = models.ForeignKey(Site, on_delete=models.PROTECT, null=True, blank=True, related_name='prefixes')
    family = models.IntegerField(choices=FAMILY_CHOICES, editable=False)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True)
    is_pool = models.BooleanField(default=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='prefixes')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_prefixes'
        ordering = ['vrf', 'prefix']
        indexes = [
            models.Index(fields=['prefix']),
            models.Index(fields=['vrf']),
        ]
        verbose_name = "Prefix"
        verbose_name_plural = "Prefixes"

    def save(self, *args, **kwargs):
        try:
            net = ipaddress.ip_network(self.prefix)
            self.family = 4 if net.version == 4 else 6
        except:
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        vrf_str = f" ({self.vrf.name})" if self.vrf else ""
        return f"{self.prefix}{vrf_str}"

    @property
    def network(self):
        try:
            return ipaddress.ip_network(self.prefix)
        except:
            return None

    @property
    def size(self):
        return self.network.num_addresses if self.network else 0

    @property
    def used_ips(self):
        return self.ipaddress_set.filter(is_deleted=False).count()

    @property
    def utilization(self):
        if self.size > 0:
            return (self.used_ips / self.size) * 100
        return 0


class IPAddress(SoftDeleteModel):
    """Individual IP address assignment"""
    IP_TYPE_CHOICES = [
        ('primary', 'Primary'), ('secondary', 'Secondary'),
        ('virtual', 'Virtual'), ('loopback', 'Loopback'),
        ('management', 'Management'), ('floating', 'Floating'),
        ('anycast', 'Anycast'), ('vip', 'VIP'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'), ('reserved', 'Reserved'),
        ('deprecated', 'Deprecated'), ('dhcp', 'DHCP'),
    ]

    address = models.GenericIPAddressField(db_index=True)
    prefix_length = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(128)])
    family = models.IntegerField(choices=[(4,'IPv4'),(6,'IPv6')], editable=False)
    vrf = models.ForeignKey(VRF, on_delete=models.PROTECT, null=True, blank=True, related_name='ip_addresses')
    interface = models.ForeignKey(Interface, on_delete=models.CASCADE, null=True, blank=True, related_name='ip_addresses')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name='ip_addresses')
    ip_type = models.CharField(max_length=50, choices=IP_TYPE_CHOICES, default='primary')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    description = models.CharField(max_length=255, blank=True)
    dns_name = models.CharField(max_length=255, blank=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='ip_addresses')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_ip_addresses'
        unique_together = ['vrf', 'address']
        indexes = [
            models.Index(fields=['address']),
            models.Index(fields=['vrf']),
        ]
        verbose_name = "IP Address"
        verbose_name_plural = "IP Addresses"

    def save(self, *args, **kwargs):
        try:
            ip = ipaddress.ip_address(self.address)
            self.family = 4 if ip.version == 4 else 6
        except:
            pass
        super().save(*args, **kwargs)

    def __str__(self):
        vrf_str = f" ({self.vrf.name})" if self.vrf else ""
        return f"{self.address}/{self.prefix_length}{vrf_str}"


# ----------------------------------------------------------------------
# 8. VLANs
# ----------------------------------------------------------------------

class VLANGroup(BaseModel):
    """Group of VLANs"""
    name = models.CharField(max_length=100)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True, related_name='vlan_groups')
    description = models.TextField(blank=True)
    min_vid = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(4094)])
    max_vid = models.IntegerField(default=4094, validators=[MinValueValidator(1), MaxValueValidator(4094)])
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_vlan_groups'
        unique_together = ['site', 'name']
        ordering = ['site', 'name']

    def __str__(self):
        return f"{self.name} ({self.site.code if self.site else 'Global'})"


class VLAN(BaseModel):
    """VLAN configuration"""
    STATUS_CHOICES = [('active','Active'), ('reserved','Reserved'), ('deprecated','Deprecated')]

    vlan_id = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(4094)])
    name = models.CharField(max_length=100)
    group = models.ForeignKey(VLANGroup, on_delete=models.PROTECT, null=True, blank=True, related_name='vlans')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='vlans')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='vlans')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_vlans'
        unique_together = ['site', 'vlan_id']
        ordering = ['site', 'vlan_id']
        indexes = [models.Index(fields=['vlan_id'])]

    def __str__(self):
        return f"VLAN {self.vlan_id} - {self.name}"


# ----------------------------------------------------------------------
# 9. WAN Circuits
# ----------------------------------------------------------------------

class Provider(BaseModel):
    """Service provider"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    account_number = models.CharField(max_length=100, blank=True)
    portal_url = models.URLField(blank=True)
    support_phone = models.CharField(max_length=50, blank=True)
    support_email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_providers'
        ordering = ['name']

    def __str__(self):
        return self.name


class Circuit(BaseModel):
    """WAN circuit"""
    CIRCUIT_TYPE_CHOICES = [
        ('ethernet', 'Ethernet'), ('mpls', 'MPLS'), ('dark_fiber', 'Dark Fiber'),
        ('dwdm', 'DWDM'), ('internet', 'Internet'),
    ]
    STATUS_CHOICES = [('active','Active'), ('planned','Planned'), ('decommissioned','Decommissioned')]

    circuit_id = models.CharField(max_length=100, unique=True)
    circuit_type = models.CharField(max_length=50, choices=CIRCUIT_TYPE_CHOICES)
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, related_name='circuits')
    site_a = models.ForeignKey(Site, on_delete=models.PROTECT, related_name='circuits_a')
    site_b = models.ForeignKey(Site, on_delete=models.PROTECT, related_name='circuits_b')
    bandwidth_mbps = models.IntegerField()
    mtu = models.IntegerField(default=1500)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    monthly_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='circuits')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_circuits'
        ordering = ['provider', 'circuit_id']

    def __str__(self):
        return f"{self.circuit_id} ({self.get_circuit_type_display()})"


class CircuitTermination(BaseModel):
    """Circuit endpoint on a device interface"""
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE, related_name='terminations')
    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name='circuit_terminations')
    interface = models.ForeignKey(Interface, on_delete=models.PROTECT, related_name='circuit_terminations')
    role = models.CharField(max_length=10, choices=[('a','A'), ('z','Z')])
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_circuit_terminations'
        unique_together = ['circuit', 'role']

    def __str__(self):
        return f"{self.circuit} - {self.role} on {self.device}:{self.interface}"


# ----------------------------------------------------------------------
# 10. BGP & Routing
# ----------------------------------------------------------------------

class ASN(BaseModel):
    """Autonomous System Number"""
    ASN_TYPE_CHOICES = [('public','Public'), ('private','Private')]

    number = models.BigIntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(4294967295)])
    asn_type = models.CharField(max_length=50, choices=ASN_TYPE_CHOICES, default='public')
    description = models.TextField(blank=True)
    organization = models.CharField(max_length=200, blank=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='asns')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_asns'
        ordering = ['number']

    def __str__(self):
        return f"AS{self.number}"

    @property
    def asdot(self):
        if self.number > 65535:
            high = self.number >> 16
            low = self.number & 65535
            return f"{high}.{low}"
        return str(self.number)


class BGPSession(BaseModel):
    """BGP peering session"""
    SESSION_TYPE_CHOICES = [('ebgp','eBGP'), ('ibgp','iBGP')]
    SESSION_STATE_CHOICES = [
        ('idle','Idle'), ('connect','Connect'), ('active','Active'),
        ('opensent','OpenSent'), ('openconfirm','OpenConfirm'), ('established','Established')
    ]

    name = models.CharField(max_length=200, blank=True)
    session_type = models.CharField(max_length=50, choices=SESSION_TYPE_CHOICES)
    device_a = models.ForeignKey(Device, on_delete=models.PROTECT, related_name='bgp_sessions_a')
    device_b = models.ForeignKey(Device, on_delete=models.PROTECT, related_name='bgp_sessions_b')
    asn_a = models.ForeignKey(ASN, on_delete=models.PROTECT, related_name='bgp_sessions_a')
    asn_b = models.ForeignKey(ASN, on_delete=models.PROTECT, related_name='bgp_sessions_b')
    ip_a = models.ForeignKey(IPAddress, on_delete=models.PROTECT, related_name='bgp_sessions_a')
    ip_b = models.ForeignKey(IPAddress, on_delete=models.PROTECT, related_name='bgp_sessions_b')
    state = models.CharField(max_length=50, choices=SESSION_STATE_CHOICES, default='idle')
    last_state_change = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_bgp_sessions'
        unique_together = ['device_a', 'device_b', 'asn_a', 'asn_b']
        verbose_name = "BGP Session"
        verbose_name_plural = "BGP Sessions"

    def __str__(self):
        return f"{self.device_a.name} (AS{self.asn_a}) ↔ {self.device_b.name} (AS{self.asn_b})"


class FHRPGroup(BaseModel):
    """First Hop Redundancy Protocol group (VRRP/HSRP)"""
    PROTOCOL_CHOICES = [('vrrp','VRRP'), ('hsrp','HSRP'), ('glbp','GLBP'), ('carp','CARP')]

    protocol = models.CharField(max_length=50, choices=PROTOCOL_CHOICES)
    group_id = models.IntegerField()
    virtual_ip = models.GenericIPAddressField()
    virtual_mac = models.CharField(max_length=17, blank=True)
    priority = models.IntegerField(default=100)
    preempt = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    vlan = models.ForeignKey(VLAN, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'inventory_fhrp_groups'
        unique_together = ['protocol', 'group_id', 'vlan']
        verbose_name = "FHRP Group"
        verbose_name_plural = "FHRP Groups"

    def __str__(self):
        return f"{self.get_protocol_display()} {self.group_id}"


# ----------------------------------------------------------------------
# 11. Virtualization
# ----------------------------------------------------------------------

class Cluster(BaseModel):
    """Virtualization cluster"""
    CLUSTER_TYPE_CHOICES = [
        ('vmware', 'VMware vSphere'), ('proxmox', 'Proxmox VE'),
        ('xen', 'XenServer'), ('kvm', 'KVM'), ('hyperv', 'Hyper-V'),
        ('nutanix', 'Nutanix'),
    ]

    name = models.CharField(max_length=100, unique=True)
    cluster_type = models.CharField(max_length=50, choices=CLUSTER_TYPE_CHOICES)
    hosts = models.ManyToManyField(Device, related_name='clusters')
    datastores = models.JSONField(default=list, blank=True)
    total_ram_gb = models.IntegerField(default=0)
    total_cpu_cores = models.IntegerField(default=0)
    total_disk_tb = models.FloatField(default=0)
    description = models.TextField(blank=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='clusters')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_clusters'
        ordering = ['name']

    def __str__(self):
        return self.name


class VirtualMachine(SoftDeleteModel):
    """Virtual machine instance"""
    POWER_STATE_CHOICES = [('running','Running'), ('stopped','Stopped'), ('suspended','Suspended')]

    name = models.CharField(max_length=100)
    cluster = models.ForeignKey(Cluster, on_delete=models.PROTECT, related_name='vms')
    host = models.ForeignKey(Device, on_delete=models.PROTECT, related_name='vms')
    vcpus = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    ram_gb = models.IntegerField(default=1)
    disk_gb = models.IntegerField(default=10)
    interfaces = models.ManyToManyField(Interface, related_name='vms', blank=True)
    ip_addresses = models.ManyToManyField(IPAddress, related_name='vms', blank=True)
    power_state = models.CharField(max_length=50, choices=POWER_STATE_CHOICES, default='stopped')
    guest_os = models.CharField(max_length=100, blank=True)
    uuid = models.CharField(max_length=36, unique=True, blank=True)
    description = models.TextField(blank=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='vms')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_virtual_machines'
        unique_together = ['cluster', 'name']
        ordering = ['cluster', 'name']

    def __str__(self):
        return f"{self.name} ({self.cluster.name})"


# ----------------------------------------------------------------------
# 12. Tenancy & Contacts
# ----------------------------------------------------------------------

class Tenant(BaseModel):
    """Customer / tenant owning resources"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    tenant_id = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children')
    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_tenants'
        ordering = ['name']

    def __str__(self):
        return self.name


class Contact(BaseModel):
    """Individual contact"""
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    tenants = models.ManyToManyField(Tenant, related_name='contacts', blank=True)
    sites = models.ManyToManyField(Site, related_name='contacts', blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_contacts'
        ordering = ['name']

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------
# 13. L2VPN Overlays (VXLAN, EVPN, VPLS)
# ----------------------------------------------------------------------

class L2VPN(BaseModel):
    """Layer 2 VPN overlay"""
    TYPE_CHOICES = [
        ('vpls', 'VPLS'), ('vxlan', 'VXLAN'), ('evpn', 'EVPN'),
        ('pbb', 'PBB'), ('vpws', 'VPWS'),
    ]

    name = models.CharField(max_length=100, unique=True)
    vpn_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    vni = models.BigIntegerField(null=True, blank=True, help_text="VXLAN Network Identifier")
    description = models.TextField(blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, null=True, blank=True, related_name='l2vpns')
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'inventory_l2vpns'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_vpn_type_display()})"
