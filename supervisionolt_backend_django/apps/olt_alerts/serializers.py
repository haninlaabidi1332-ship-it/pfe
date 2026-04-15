from rest_framework import serializers
from .models import AlertPolicy, ActiveAlert, NotificationChannel

class AlertPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertPolicy
        fields = '__all__'

class ActiveAlertSerializer(serializers.ModelSerializer):
    olt_name = serializers.CharField(source='olt.name', read_only=True)
    class Meta:
        model = ActiveAlert
        fields = '__all__'

class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = '__all__'