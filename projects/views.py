
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from accounts.models import User
from core.throttles import ProjectCreateRateThrottle
from .models import Project
from .serializers import ProjectSerializer, AssignUserSerializer
from core.permissions import isManagerOrAdmin, isAnyRole, isSameCompany, isAdmin
from core.utils import log_audit
from core.tasks import send_project_assignment_email

# class to handle get and post requests for projects
class ProjectListCreateView(APIView):
    # apply throttle only to POST requests for project creation
    def get_throttles(self):
        if self.request.method == 'POST':
            return [ProjectCreateRateThrottle()]
        return []
    
    # set permissions based on request method
    def get_permissions(self):
        if self.request.method == 'POST':
            return [isManagerOrAdmin(), isSameCompany()]
        return [isAnyRole(), isSameCompany()]
    # get method to list projects 
    def get(self, request):
        company = request.user.company
        
        if request.user.role in ['admin', 'manager']:
            projects = Project.objects.filter(company=company)
        else:
            projects = request.user.assigned_projects.filter(is_deleted=False)
        
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)
    
    
    # creates new project
    
    @transaction.atomic
    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        project = Project.objects.create(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            company=request.user.company,
            created_by=request.user
        )
        
        project.members.add(request.user)
        
        # Auto-add all admins
        admins = User.objects.filter(company=request.user.company, role='admin')
        for admin in admins:
            project.members.add(admin)
        
        log_audit(request.user, 'CREATE', 'Project', project.id, project.name,
                  {'name': project.name, 'description': project.description}, request)
        
        response_serializer = ProjectSerializer(project)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

# Handles:GET single project, UPDATE project, DELETE project

class ProjectDetailView(APIView):
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [isAnyRole(), isSameCompany()]
        return [isManagerOrAdmin(), isSameCompany()]
    
    def get_project(self, project_id, company):
        try:
            return Project.objects.get(id=project_id, company=company, is_deleted=False)
        except Project.DoesNotExist:
            return None
    
    def get(self, request, project_id):
        project = self.get_project(project_id, request.user.company)
        
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role == 'employee' and request.user not in project.members.all():
            return Response({"error": "You don't have access to this project"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProjectSerializer(project)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, project_id):
        if request.user.role == 'employee':
            return Response(
                {"error": "Employees cannot update projects"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        project = self.get_project(project_id, request.user.company)
        
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        old_data = {'name': project.name, 'description': project.description}
        
        if 'name' in request.data:
            project.name = request.data['name']
        if 'description' in request.data:
            project.description = request.data['description']
        
        project.save()
        
        log_audit(request.user, 'UPDATE', 'Project', project.id, project.name,
                  {'old': old_data, 'new': {'name': project.name, 'description': project.description}}, request)
        
        serializer = ProjectSerializer(project)
        return Response(serializer.data)
    
    @transaction.atomic
    def delete(self, request, project_id):
     """Soft delete a project - marks as deleted instead of removing"""
     if request.user.role == 'employee':
        return Response(
            {"error": "Employees cannot delete projects"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Use all_objects to find even if already deleted
     try:
        project = Project.all_objects.get(id=project_id, company=request.user.company)
     except Project.DoesNotExist:
        return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if already deleted
     if project.is_deleted:
        return Response(
            {"error": "Project is already deleted"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
     project_name = project.name
    
    # Soft delete the project
     project.soft_delete()
    
     log_audit(request.user, 'SOFT_DELETE', 'Project', project_id, project_name,
              {'message': f'Project "{project_name}" soft deleted at {project.deleted_at}'}, request)
    
     return Response({
        "message": f"Project '{project_name}' has been soft deleted. Use /restore/ to recover."
    }, status=status.HTTP_200_OK)

# assign users to projects

class AssignUserToProjectView(APIView):
    permission_classes = [isManagerOrAdmin, isSameCompany]
    
    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, company=request.user.company)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AssignUserSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = serializer.validated_data['user_id']
        
        try:
            user = User.objects.get(id=user_id, company=request.user.company)
        except User.DoesNotExist:
            return Response({"error": "User not found in your company"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        project.members.add(user)
        # Send email only to the user being assigned
        
        send_project_assignment_email.delay(
            project_id=project.id,
            assigned_to_email=user.email,
            assigned_by_email=request.user.email,
            project_name=project.name,
            company_name=request.user.company.name
        )
        
        log_audit(request.user, 'UPDATE', 'Project', project.id, project.name,
                  {'action': f'Added user {user.email} to project'}, request)
        
        return Response({
            "message": f"User {user.email} assigned to project {project.name} successfully"
        }, status=status.HTTP_200_OK)
        


# Handles: Restore soft deleted project, List soft deleted projects (Admin only)

class RestoreProjectView(APIView):
    """Restore a soft deleted project - Admin only"""
    permission_classes = [isAdmin, isSameCompany]
    
    @transaction.atomic
    def post(self, request, project_id):
        try:
            # Use all_objects to find deleted projects
            project = Project.all_objects.get(id=project_id, company=request.user.company)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if it's actually deleted
        if not project.is_deleted:
            return Response(
                {"error": "Project is not deleted. Nothing to restore."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project_name = project.name
        
        # Restore the project
        project.restore()
        
        from django.utils import timezone
        log_audit(request.user, 'RESTORE', 'Project', project_id, project_name,
                  {'message': f'Project "{project_name}" restored from trash'}, request)
        
        return Response({
            "message": f"Project '{project_name}' has been restored successfully."
        }, status=status.HTTP_200_OK)

# List soft deleted projects - Admin only
class DeletedProjectsListView(APIView):
    """List all soft deleted projects - Admin only"""
    permission_classes = [isAdmin, isSameCompany]
    
    def get(self, request):
        # Use all_objects and filter by is_deleted=True
        deleted_projects = Project.all_objects.filter(
            company=request.user.company,
            is_deleted=True
        )
        
        from .serializers import DeletedProjectSerializer
        serializer = DeletedProjectSerializer(deleted_projects, many=True)
        return Response({
            "count": deleted_projects.count(),
            "deleted_projects": serializer.data
        })