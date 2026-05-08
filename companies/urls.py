from django.urls import path
from . import views

urlpatterns = [
    # url for registering new 
    path('api/companies/register/', views.CompanyRegisterView.as_view(), name='company-register'),
]