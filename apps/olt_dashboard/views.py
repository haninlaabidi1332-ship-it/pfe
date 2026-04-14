from rest_framework.views import APIView
from rest_framework.response import Response
from apps.olt_inventory.models import Device, ONU
from apps.olt_alerts.models import ActiveAlert
from django.db.models import Count

class GlobalStatsView(APIView):
    """Vue qui regroupe les stats pour le dashboard principal"""
    
    def get(self, request):
        # 1. Stats Inventaire
        total_olts = Device.objects.count()
        total_onus = ONU.objects.count()
        
        # 2. Stats Alertes (provenant de olt_alerts)
        active_alerts_count = ActiveAlert.objects.count()
        critical_alerts = ActiveAlert.objects.filter(policy__severity='critical').count()
        
        # 3. Distribution par statut (OLTs)
        status_dist = Device.objects.values('status').annotate(total=Count('status'))

        data = {
            "inventory": {
                "total_olts": total_olts,
                "total_onus": total_onus,
            },
            "health": {
                "active_alerts": active_alerts_count,
                "critical_issues": critical_alerts,
                "system_status": "Degraded" if critical_alerts > 0 else "Optimal"
            },
            "status_distribution": status_dist
        }
        return Response(data)