from rest_framework import serializers
from .models import SNMPMetric, BFDSession, PerformanceMetric

class SNMPMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SNMPMetric
        fields = '__all__'

class BFDSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BFDSession
        fields = '__all__'

class PerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetric
        fields = '__all__'