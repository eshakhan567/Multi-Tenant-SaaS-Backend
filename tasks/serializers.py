from rest_framework import serializers

from .models import Task




# Serializer for Task model
class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'project', 'project_name', 'company', 'title', 'description', 
                  'assigned_to', 'assigned_to_email', 'status', 'status_display', 
                  'created_by', 'created_by_email', 'created_at', 'updated_at', 'is_deleted', 'deleted_at']
        read_only_fields = ['id', 'project', 'company', 'created_by', 'created_at', 'updated_at', 'is_deleted', 'deleted_at']
      
      
      
        # serializer for deeleted tasks 

class DeletedTaskSerializer(serializers.ModelSerializer):
   
    project_name = serializers.CharField(source='project.name', read_only=True)
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'project_name', 'assigned_to_email',
                  'status', 'company_name', 'created_at', 'deleted_at']
        read_only_fields = ['id', 'project', 'company', 'created_by', 'created_at', 'updated_at', 'is_deleted', 'deleted_at']