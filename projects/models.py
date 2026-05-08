from django.db import models
from companies.models import Company
from accounts.models import User


# Custom Manager for active projects (not deleted)
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

# Custom Manager for all projects (including deleted)
class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

# Project Model
class Project(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    members = models.ManyToManyField(User, related_name='assigned_projects', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_deleted = models.BooleanField(default=False)  # True = deleted
    deleted_at = models.DateTimeField(null=True, blank=True)  # When deleted
    
    # Managers
    objects = ActiveManager()  # returns only active projects
    all_objects = AllObjectsManager()  # Returns all projects (including deleted)
    
    class Meta:
        ordering = ['-created_at']
    
    def soft_delete(self):
        """Mark project as deleted"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    # Method to restore a soft-deleted project
    def restore(self):
       
        self.is_deleted = False
        self.deleted_at = None
        self.save()
    # Method to permanently delete a project from the database
    def hard_delete(self):
       
        super().delete()
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"