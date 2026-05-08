from django.db import models
from companies.models import Company
from accounts.models import User
from projects.models import Project


# Custom Manager to return only active (non-deleted) tasks
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

# Custom Manager for all tasks
class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()
# Task model with soft delete functionality
class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_deleted = models.BooleanField(default=False)  # True = deleted
    deleted_at = models.DateTimeField(null=True, blank=True)  # When deleted
    
    # Managers
    objects = ActiveManager()  # returns only active tasks
    all_objects = AllObjectsManager()  # Returns ALL tasks (including deleted)
    
    class Meta:
        ordering = ['-created_at']
    # Soft delete method
    def soft_delete(self):
        
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    # Restore method to undo soft delete
    def restore(self):
       
        self.is_deleted = False
        self.deleted_at = None
        self.save()
    # Hard delete method to permanently remove the task from the database
    def hard_delete(self):
        
        super().delete()
    
    def __str__(self):
        return f"{self.title} - {self.status}"