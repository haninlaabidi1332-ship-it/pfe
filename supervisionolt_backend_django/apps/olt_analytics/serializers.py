from rest_framework import serializers
from .models import NetworkReport, AlertHistory

class NetworkReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkReport
        fields = '__all__'

class AlertHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertHistory
        fields = '__all__'