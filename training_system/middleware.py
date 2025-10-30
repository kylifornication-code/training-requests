"""
Custom middleware for the training system application.
"""
from django.http import HttpResponsePermanentRedirect
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add Content Security Policy for enhanced security
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self';"
            )
        
        return response


class RequestLoggingMiddleware:
    """
    Middleware to log requests for security monitoring.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details for security monitoring
        if not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            logger.info(
                f"Request: {request.method} {request.path} "
                f"from {request.META.get('REMOTE_ADDR', 'unknown')} "
                f"User: {request.user.username if request.user.is_authenticated else 'anonymous'}"
            )
        
        response = self.get_response(request)
        return response


class HTTPSRedirectMiddleware:
    """
    Middleware to redirect HTTP requests to HTTPS in production.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only redirect to HTTPS in production
        if not settings.DEBUG and not request.is_secure():
            if request.META.get('HTTP_X_FORWARDED_PROTO') != 'https':
                return HttpResponsePermanentRedirect(
                    f"https://{request.get_host()}{request.get_full_path()}"
                )
        
        response = self.get_response(request)
        return response


class RateLimitMiddleware:
    """
    Simple rate limiting middleware to prevent abuse.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        self.window_size = 60  # 1 minute window
        self.max_requests = 100  # Max requests per window

    def __call__(self, request):
        # Skip rate limiting for static files and admin
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.startswith('/admin/')):
            return self.get_response(request)
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        current_time = timezone.now().timestamp()
        
        # Clean old entries
        self.cleanup_old_entries(current_time)
        
        # Check rate limit
        if client_ip in self.request_counts:
            if len(self.request_counts[client_ip]) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                from django.http import HttpResponseTooManyRequests
                return HttpResponseTooManyRequests("Rate limit exceeded. Please try again later.")
        
        # Record request
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        self.request_counts[client_ip].append(current_time)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def cleanup_old_entries(self, current_time):
        """Remove entries older than the window size."""
        cutoff_time = current_time - self.window_size
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip] = [
                timestamp for timestamp in self.request_counts[ip]
                if timestamp > cutoff_time
            ]
            if not self.request_counts[ip]:
                del self.request_counts[ip]


class URLValidationMiddleware:
    """
    Middleware to validate and secure URL patterns.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Define protected URL patterns that require authentication
        self.protected_patterns = [
            '/dashboard/',
            '/requests/',
            '/pending/',
            '/leadership/',
            '/statistics/',
            '/completed/',
            '/users/',
            '/admin/',
        ]
        
        # Define public URL patterns that don't require authentication
        self.public_patterns = [
            '/login/',
            '/logout/',
            '/register/',
            '/password_reset/',
            '/reset/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]

    def __call__(self, request):
        # Check if URL requires authentication
        if self.requires_authentication(request.path):
            if not request.user.is_authenticated:
                # Let Django's authentication system handle the redirect
                pass
        
        # Log suspicious URL patterns
        if self.is_suspicious_url(request.path):
            logger.warning(
                f"Suspicious URL access attempt: {request.path} "
                f"from {request.META.get('REMOTE_ADDR', 'unknown')} "
                f"User: {request.user.username if request.user.is_authenticated else 'anonymous'}"
            )
        
        response = self.get_response(request)
        return response
    
    def requires_authentication(self, path):
        """Check if a URL path requires authentication."""
        return any(path.startswith(pattern) for pattern in self.protected_patterns)
    
    def is_suspicious_url(self, path):
        """Check if a URL path looks suspicious."""
        suspicious_patterns = [
            '/.env',
            '/wp-admin/',
            '/admin.php',
            '/phpmyadmin/',
            '/.git/',
            '/config/',
            '/backup/',
            '/test/',
            '/debug/',
        ]
        return any(pattern in path.lower() for pattern in suspicious_patterns)


class CSRFEnhancementMiddleware:
    """
    Enhanced CSRF protection middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add additional CSRF validation for AJAX requests
        # Check for AJAX request using HTTP_X_REQUESTED_WITH header (modern approach)
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        if is_ajax and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            csrf_token = request.META.get('HTTP_X_CSRFTOKEN')
            if not csrf_token:
                logger.warning(
                    f"AJAX request without CSRF token from {request.META.get('REMOTE_ADDR', 'unknown')}"
                )
        
        response = self.get_response(request)
        
        # Add CSRF token to response headers for AJAX requests
        if hasattr(request, 'META') and 'HTTP_X_REQUESTED_WITH' in request.META:
            from django.middleware.csrf import get_token
            response['X-CSRFToken'] = get_token(request)
        
        return response