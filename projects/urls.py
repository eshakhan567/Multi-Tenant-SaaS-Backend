from django.urls import path
from . import views

urlpatterns = [
    
    path('api/projects/', views.ProjectListCreateView.as_view(), name='project-list-create'),
    path('api/projects/<int:project_id>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('api/projects/<int:project_id>/assign/', views.AssignUserToProjectView.as_view(), name='assign-user'),
    
    
    path('api/projects/<int:project_id>/restore/', views.RestoreProjectView.as_view(), name='restore-project'),
    path('api/projects/deleted/', views.DeletedProjectsListView.as_view(), name='deleted-projects'),
    
]