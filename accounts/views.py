from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from .models import User
from .serializers import LoginSerializer, UserSerializer, CreateUserSerializer
from core.permissions import isAdmin, isSameCompany,isAnyRole
from rest_framework_simplejwt.exceptions import TokenError
from core.tasks import send_welcome_email
from core.throttles import LoginRateThrottle


# function to log audit data for user actions

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

# class to handle user login API

class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]  
    
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        log_audit(user, 'LOGIN', 'User', user.id, user.email, {}, request)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'company': user.company.name
            }
        }, status=status.HTTP_200_OK)

# class to handle user logout API
class LogoutView(APIView):
    
    permission_classes = [isAnyRole, isSameCompany]
    
    def post(self, request):
        try:
            from audit.models import AuditLog
            
            # Get IP address
            ip_address = None
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Create audit log
            AuditLog.objects.create(
                company=request.user.company,
                user=request.user,
                action='LOGOUT',
                model_name='User',
                object_id=request.user.id,
                object_repr=request.user.email,
                changes={'message': 'User logged out'},
                ip_address=ip_address
            )
            
            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
# class to manage users by admins only

class ManageUsersView(APIView):
    permission_classes = [isAdmin, isSameCompany]
    
    
    def get(self, request):
        
        users = User.objects.filter(company=request.user.company)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            company=request.user.company,
            role=serializer.validated_data['role']
        )
        
        
        #  welcome email after user creation
        send_welcome_email.delay(
            user_email=user.email,
            company_name=request.user.company.name,
            user_name=user.email.split('@')[0],
            user_role=user.role
        )
        
        
        log_audit(request.user, 'CREATE', 'User', user.id, user.email,
                  {'email': user.email, 'role': user.role}, request)
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )
    # function to delete users
    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, company=request.user.company)
            if user.role == 'admin':
                return Response(
                    {"error": "Cannot delete admin user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user_email = user.email
            user.delete()
            
            log_audit(request.user, 'DELETE', 'User', user_id, user_email, {}, request)
            
            return Response(
                {"message": "User deleted successfully"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
