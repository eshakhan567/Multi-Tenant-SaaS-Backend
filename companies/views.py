from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from core.throttles import RegisterRateThrottle
from .models import Company
from .serializers import CompanyRegisterSerializer
from accounts.models import User

# Utility function to log audit actions
def log_audit(user, action, model_name, object_id, object_repr, changes=None, request=None):
    from audit.models import AuditLog
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    AuditLog.objects.create(
        company=user.company,
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        changes=changes or {},
        ip_address=ip_address
    )

# API view for company registration
class CompanyRegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle] 
    
    @transaction.atomic
    def post(self, request):
        serializer = CompanyRegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        company = Company.objects.create(name=validated_data['company_name'])
        
        admin_user = User.objects.create_user(
            email=validated_data['admin_email'],
            password=validated_data['admin_password'],
            company=company,
            role='admin',
            is_staff=True
        )
        
        log_audit(admin_user, 'CREATE', 'Company', company.id, company.name,
                  {'company_name': company.name, 'admin_email': admin_user.email}, request)
        
        return Response({
            "message": "Company registered successfully",
            "company": company.name,
            "admin": admin_user.email
        }, status=status.HTTP_201_CREATED)
