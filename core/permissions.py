from rest_framework import permissions


# custom permissions for admin role
class isAdmin(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        return request.user.role == 'admin'

# custom permissions for manager role
class isManagerOrAdmin(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'manager']

# custom permissions for any role users
class isAnyRole(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'manager', 'employee']

# custom permissions for company data access
class isSameCompany(permissions.BasePermission):
   
    def has_permission(self, request, view):
        return True
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        elif hasattr(obj, 'project') and hasattr(obj.project, 'company'):
            return obj.project.company == request.user.company
        elif hasattr(obj, 'user') and hasattr(obj.user, 'company'):
            return obj.user.company == request.user.company
        return False
