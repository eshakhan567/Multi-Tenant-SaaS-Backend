from rest_framework import serializers
from .models import AuditLog


# convert audit logs to human readable format for API responses
class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'company', 'company_name', 'user', 'user_email', 
            'action', 'model_name', 'object_id', 'object_repr', 
            'changes', 'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']