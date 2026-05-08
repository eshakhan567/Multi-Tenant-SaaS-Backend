from django.urls import path
from . import views

urlpatterns = [
    path('api/projects/<int:project_id>/tasks/', views.TaskListCreateView.as_view(), name='task-list-create'),
    path('api/projects/<int:project_id>/tasks/<int:task_id>/', views.TaskDetailView.as_view(), name='task-detail'),
    
    path('api/tasks/<int:task_id>/restore/', views.RestoreTaskView.as_view(), name='restore-task'),
    path('api/tasks/deleted/', views.DeletedTasksListView.as_view(), name='deleted-tasks'),
    path('api/tasks/<int:task_id>/assign/', views.TaskAssignView.as_view(), name='task-assign'),
]