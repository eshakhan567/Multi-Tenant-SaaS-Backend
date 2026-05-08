from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # url for login
    path('api/auth/login/', views.LoginView.as_view(), name='login'),
    # url for logout
    path('api/auth/logout/', views.LogoutView.as_view(), name='logout'),
    # url for token refresh
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    # url for listing users
    path('api/users/', views.ManageUsersView.as_view(), name='list-create-users'),
    # url for deleting user by id
    path('api/users/<int:user_id>/', views.ManageUsersView.as_view(), name='delete-user'),
]
