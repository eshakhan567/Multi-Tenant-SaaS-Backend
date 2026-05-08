from rest_framework import serializers
from .models import Company


# company model used for API responses
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

# registers new company along with admin user creation

class CompanyRegisterSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    admin_email = serializers.EmailField()
    admin_password = serializers.CharField(write_only=True, min_length=6)
    
    def validate_company_name(self, value):
        if Company.objects.filter(name=value).exists():
            raise serializers.ValidationError("Company name already exists")
        return value