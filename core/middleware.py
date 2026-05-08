from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import JsonResponse
import time

# custom middleware for global rate limiting
class GlobalRateLimitMiddleware(MiddlewareMixin):
    
    
    # runs automatically for every incoming request
    def process_request(self, request):
        # Skip for admin URLs
        if request.path.startswith('/admin/'):
            return None
        
        # Get client IP
        ip = self.get_client_ip(request)
        cache_key = f"global_rate_limit_{ip}"
        
        # Get request count
        current = cache.get(cache_key, 0)
        
        # Limit: 200 requests per minute per IP (DDoS protection)
        if current > 200:
            return JsonResponse(
                {"error": "Too many requests. Please try again later."},
                status=429
            )
        
        # Increment counter
        cache.set(cache_key, current + 1, 60)  # Reset after 60 seconds
        
        return None
    
    
    # Gets user's IP address
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip