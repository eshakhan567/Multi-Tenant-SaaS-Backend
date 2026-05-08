from rest_framework.views import APIView
from rest_framework.response import Response

from core.tasks import log_user_activity_async
from .models import AuditLog
from .serializers import AuditLogSerializer
from core.permissions import isAdmin, isAnyRole, isSameCompany
from core.throttles import AuditLogRateThrottle

# API endpoint to view all audit logs
class AuditLogView(APIView):
    """View audit logs (Admin only)"""
    permission_classes = [isAdmin, isSameCompany]
    throttle_classes = [AuditLogRateThrottle] 

    def get(self, request):
        logs = AuditLog.objects.filter(company=request.user.company)
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)

# class to view activity logs of user's own actions
class MyActivityView(APIView):
   
    permission_classes = [isAnyRole, isSameCompany]
    
    def get(self, request):
        logs = AuditLog.objects.filter(user=request.user, company=request.user.company)
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)
    
# background logging
class AsyncAuditLogView(APIView):    
    def post(self, request):
        
        log_user_activity_async.delay(
            user_id=request.user.id,
            action='CUSTOM_ACTION',
            model_name='CustomModel',
            object_id=request.data.get('id'),
            object_repr=request.data.get('name'),
            changes=request.data,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({"message": "Action logged in background"}, status=200)