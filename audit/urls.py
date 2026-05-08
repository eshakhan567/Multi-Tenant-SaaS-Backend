from django.urls import path
from . import views

urlpatterns = [
    # url for checking all audit logs (admin only)
    path('api/audit-logs/', views.AuditLogView.as_view(), name='audit-logs'),
    
    # url for checking own activity logs (all users)
    path('api/my-activity/', views.MyActivityView.as_view(), name='my-activity'),
]