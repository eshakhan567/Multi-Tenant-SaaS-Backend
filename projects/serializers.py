from rest_framework import serializers
from .models import Project


# Serializer for Project model
class ProjectSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    members_count = serializers.IntegerField(source='members.count', read_only=True)
    tasks_count = serializers.IntegerField(source='tasks.count', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'company', 'created_by', 'created_by_email', 
                  'members', 'members_count', 'tasks_count', 'created_at', 'updated_at','is_deleted', 'deleted_at']
        read_only_fields = ['id', 'company', 'created_by', 'created_at', 'updated_at', 'is_deleted', 'deleted_at']

# Serializer for creating/updating projects
class DeletedProjectSerializer(serializers.ModelSerializer):
    """Serializer for deleted projects (includes deletion info)"""
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'company_name', 'created_by_email', 
                  'created_at', 'deleted_at']
        read_only_fields = ['id', 'company', 'created_by', 'created_at', 'updated_at', 'is_deleted', 'deleted_at']

# Serializer for assigning users to projects
class AssignUserSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        from accounts.models import User
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")