from urllib import request

from django.tasks import task
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from accounts.models import User
from core.throttles import TaskCreateRateThrottle
from projects.models import Project
from .models import Task
from django.utils import timezone
from .serializers import TaskSerializer, DeletedTaskSerializer
from core.permissions import isManagerOrAdmin, isAnyRole, isSameCompany,isAdmin
from core.utils import log_audit
from core.tasks import send_task_assignment_email, send_task_status_update_notification

# class to handle get and post requests for tasks within a project
class TaskListCreateView(APIView):
    
    def get_throttles(self):
        if self.request.method == 'POST':
            return [TaskCreateRateThrottle()]
        return []
        
    def get_permissions(self):
        if self.request.method == 'POST':
            return [isManagerOrAdmin(), isSameCompany()]
        return [isAnyRole(), isSameCompany()]
    
    def get_project(self, project_id, company):
        try:
            return Project.objects.get(id=project_id, company=company,is_deleted=False)
        except Project.DoesNotExist:
            return None
    
    def get(self, request, project_id):
        project = self.get_project(project_id, request.user.company)
        
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role in ['admin', 'manager']:
            tasks = Task.objects.filter(project=project, company=request.user.company, is_deleted=False)
        else:
            tasks = Task.objects.filter(project=project, assigned_to=request.user, company=request.user.company, is_deleted=False)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    # creates new task within a project
    
    @transaction.atomic
    def post(self, request, project_id):
        project = self.get_project(project_id, request.user.company)
        
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TaskSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        assigned_to_id = serializer.validated_data.get('assigned_to')
        assigned_to = None
        
        if assigned_to_id:
            try:
                assigned_to = User.objects.get(id=assigned_to_id.id, company=request.user.company)
            except User.DoesNotExist:
                return Response({"error": "Assigned user not found in your company"}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        task = Task.objects.create(
            project=project,
            company=request.user.company,
            title=serializer.validated_data['title'],
            description=serializer.validated_data.get('description', ''),
            assigned_to=assigned_to,
            status='pending',
            created_by=request.user
        )
        
        if assigned_to:
            send_task_assignment_email.delay(
            task_id=task.id,
            assigned_to_email=assigned_to.email,
            assigned_by_email=request.user.email,
            task_title=task.title,
            project_name=project.name,
            company_id=request.user.company.id
    )
        


        
        log_audit(request.user, 'CREATE', 'Task', task.id, task.title,
                  {'title': task.title, 'project': project.name, 
                   'assigned_to': assigned_to.email if assigned_to else None}, request)
        
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

# Handles:GET single task, UPDATE task, DELETE task

class TaskDetailView(APIView):
    
    def get_task(self, task_id, company):
        try:
            return Task.objects.get(id=task_id, company=company, is_deleted=False)
        except Task.DoesNotExist:
            return None
    
    def get(self, request, project_id, task_id):
        task = self.get_task(task_id, request.user.company)
        
        if not task or task.project.id != project_id:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.role == 'employee' and task.assigned_to != request.user:
            return Response({"error": "You don't have access to this task"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    # updates tasks details such as title, description, assigned user, and status
    @transaction.atomic
    def put(self, request, project_id, task_id):
        task = self.get_task(task_id, request.user.company)
        
        if not task or task.project.id != project_id:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        old_data = {'title': task.title, 'description': task.description, 'status': task.status}
        if request.user.role == 'employee':
    # Check if task is assigned to this employee
            if task.assigned_to != request.user:
                return Response({"error": "You can only update tasks assigned to you"}, 
                      status=status.HTTP_403_FORBIDDEN)
    
    # Check ALL fields the employee is trying to update
            allowed_fields = ['status']
            forbidden_fields = []
    
            for field in request.data.keys():
                if field not in allowed_fields:
                    forbidden_fields.append(field)
    
    # If trying to update any field other than 'status', show error
            if forbidden_fields:
                return Response({
             "error": f"Employees can only update task status. Cannot update: {', '.join(forbidden_fields)}"
        }, status=status.HTTP_403_FORBIDDEN)
    
        if 'title' in request.data and request.user.role != 'employee':
            task.title = request.data['title']
        if 'description' in request.data and request.user.role != 'employee':
            task.description = request.data['description']
        if 'assigned_to' in request.data and request.user.role != 'employee':
            assigned_to_id = request.data['assigned_to']
            if assigned_to_id:
                try:
                    assigned_to = User.objects.get(id=assigned_to_id, company=request.user.company)
                    task.assigned_to = assigned_to
                except User.DoesNotExist:
                    return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        if 'status' in request.data:
            task.status = request.data['status']
        
        task.save()
        
        # Send notification when task status changes 
        if 'status' in request.data and task.status != old_data.get('status'):
            if task.assigned_to:
                send_task_status_update_notification.delay(
                    task_id=task.id,
                    task_title=task.title,
                    new_status=task.status,
                    updated_by_email=request.user.email,
                    assigned_to_email=task.assigned_to.email
        )
        
        
        log_audit(request.user, 'UPDATE', 'Task', task.id, task.title,
                  {'old': old_data, 'new': {'title': task.title, 'status': task.status}}, request)
        
        serializer = TaskSerializer(task)
        return Response(serializer.data)
     
    
    
 # soft delete a task - marks as deleted instead of removing from database
    @transaction.atomic
    def delete(self, request, project_id, task_id):
        """Soft delete a task - marks as deleted instead of removing"""
        if request.user.role == 'employee':
            return Response({"error": "Employees cannot delete tasks"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        try:
            task = Task.all_objects.get(id=task_id, company=request.user.company)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if task.project.id != project_id:
            return Response({"error": "Task not found in this project"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        if task.is_deleted:
            return Response(
                {"error": "Task is already deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.soft_delete()
        
        log_audit(request.user, 'SOFT_DELETE', 'Task', task.id, task.title,
                  {'message': f'Task "{task.title}" soft deleted at {task.deleted_at}'}, request)
        
        return Response({
            "message": f"Task '{task.title}' has been soft deleted. Use /restore/ to recover.",
            "deleted_at": task.deleted_at
        }, status=status.HTTP_200_OK)

# assign task to user with background email notification
class TaskAssignView(APIView):
    
    permission_classes = [isManagerOrAdmin, isSameCompany]
    
    @transaction.atomic
    def post(self, request, task_id):

        
        try:
            task = Task.objects.get(id=task_id, company=request.user.company)
          
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        assigned_to_id = request.data.get('assigned_to')
        
        
        try:
            assigned_to = User.objects.get(id=assigned_to_id, company=request.user.company)
             
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Assign the task
        task.assigned_to = assigned_to
        task.save()
        
        # Send email to assigned user 
        send_task_assignment_email.delay(
            task_id=task.id,
            assigned_to_email=assigned_to.email,
            assigned_by_email=request.user.email,
            task_title=task.title,
            project_name=task.project.name,
            company_id=request.user.company.id
        )
        
        
        
        log_audit(request.user, 'ASSIGN', 'Task', task.id, task.title,
                  {'assigned_to': assigned_to.email}, request)
        
        return Response({
            "message": f"Task '{task.title}' assigned to {assigned_to.email}",
            "email_notification": "Queued for background sending"
        }, status=status.HTTP_200_OK)
        
        # restore views for tasks (Admin only)
class RestoreTaskView(APIView):
   
    permission_classes = [isAdmin, isSameCompany]
    
    @transaction.atomic
    def post(self, request, task_id):
        try:
            task = Task.all_objects.get(id=task_id, company=request.user.company)
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not task.is_deleted:
            return Response(
                {"error": "Task is not deleted. Nothing to restore."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.restore()
        
        log_audit(request.user, 'RESTORE', 'Task', task.id, task.title,
                  {'message': f'Task "{task.title}" restored from trash'}, request)
        
        return Response({
            "message": f"Task '{task.title}' has been restored successfully.",
            "restored_at": timezone.now()
        }, status=status.HTTP_200_OK)

# list all soft deleted tasks - Admin only
class DeletedTasksListView(APIView):
    
    permission_classes = [isAdmin, isSameCompany]
    
    def get(self, request):
        deleted_tasks = Task.all_objects.filter(
            company=request.user.company,
            is_deleted=True
        )
        
        serializer = DeletedTaskSerializer(deleted_tasks, many=True)
        return Response({
            "count": deleted_tasks.count(),
            "deleted_tasks": serializer.data
        })
