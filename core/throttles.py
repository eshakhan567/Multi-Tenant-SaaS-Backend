from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle



# login throttle to limit login attempts : 5 per minute per IP address
class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'
    
    def get_cache_key(self, request, view):
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Create cache key based on IP
        return f"login_attempts_{ip}"

# register throttle to limit registration attempts : 10 per hour per IP address
class RegisterRateThrottle(SimpleRateThrottle):
    scope = 'register'
    rate = '10/hour'  
    
    def get_cache_key(self, request, view):
        # Rate limit by IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return f"register_throttle_{ip}"

# throttle for project creation - 50 per hour per user
class ProjectCreateRateThrottle(SimpleRateThrottle):  
    
    scope = 'project_create'
    rate = '50/hour'  
    
    def get_cache_key(self, request, view):
        
        if request.method == 'POST' and request.user and request.user.is_authenticated:
            # Rate limit by user ID
            return f"project_create_{request.user.id}"
        return None
# throttle for task creation - 100 per hour per user

class TaskCreateRateThrottle(SimpleRateThrottle):
   
    scope = 'task_create'
    rate = '100/hour'  
    
    def get_cache_key(self, request, view):
        
        if request.method == 'POST' and request.user and request.user.is_authenticated:
            return f"task_create_{request.user.id}"
        return None

# throttle for admin users - 1000 requests per hour per user 
    
class AdminUserRateThrottle(SimpleRateThrottle):
    
    scope = 'admin'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated and request.user.role == 'admin':
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.id
            }
        return None 

# throttle for audit log access - 20 requests per minute per user 
class AuditLogRateThrottle(SimpleRateThrottle):
    
    scope = 'audit_logs'
    rate = '20/minute'  
    
    def get_cache_key(self, request, view):
        
        if request.method == 'GET' and request.user and request.user.is_authenticated:
            # Rate limit by user ID
            return f"audit_logs_{request.user.id}"
        return None
    
# throttle for user list access - 30 requests per minute per user
 
class UserListRateThrottle(SimpleRateThrottle):
    scope = 'user_list'
    rate = '30/minute'
    def get_cache_key(self, request, view):
        if request.method == 'GET' and request.user and request.user.is_authenticated:
            cache_key = self.cache_format % {
                'scope': self.scope,
                'ident': request.user.id
            }
            
            return cache_key
        return None
    
    