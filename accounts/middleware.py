from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import PermissionDenied


class RoleBasedAccessMiddleware:
    """
    Middleware to enforce role-based access control across the application.
    This middleware checks user roles for specific URL patterns and redirects
    unauthorized users appropriately.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define URL patterns that require specific roles
        self.role_patterns = {
            '/admin/': ['ADMIN'],
            '/leadership/': ['LEADERSHIP', 'ADMIN'],
            '/reports/': ['LEADERSHIP', 'ADMIN'],
            '/users/': ['LEADERSHIP', 'ADMIN'],
        }

    def __call__(self, request):
        # Process the request before the view
        response = self.process_request(request)
        if response:
            return response
        
        # Get the response from the view
        response = self.get_response(request)
        return response

    def process_request(self, request):
        """Check if the user has permission to access the requested URL"""
        
        # Skip authentication checks for certain paths
        skip_paths = [
            '/login/',
            '/logout/',
            '/register/',
            '/password_reset/',
            '/static/',
            '/media/',
            '/health/',  # Health check endpoint for monitoring
        ]
        
        # Check if the path should be skipped
        for skip_path in skip_paths:
            if request.path.startswith(skip_path):
                return None
        
        # Check if user is authenticated for protected paths
        if not request.user.is_authenticated:
            # Allow access to public paths
            public_paths = ['/', '/dashboard/']
            if request.path not in public_paths:
                return redirect('accounts:login')
            return None
        
        # Check role-based access for specific patterns
        for pattern, required_roles in self.role_patterns.items():
            if request.path.startswith(pattern):
                if not hasattr(request.user, 'userprofile'):
                    messages.error(request, 'Access denied: No user profile found.')
                    return redirect('accounts:login')
                
                user_role = request.user.userprofile.role
                if user_role not in required_roles:
                    messages.error(request, 'Access denied: Insufficient permissions.')
                    return redirect('dashboard')
        
        return None


class UserProfileMiddleware:
    """
    Middleware to ensure all authenticated users have a UserProfile.
    This middleware creates a UserProfile if one doesn't exist for an authenticated user.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and has a profile
        if request.user.is_authenticated and not hasattr(request.user, 'userprofile'):
            from .models import UserProfile
            # Create a default UserProfile for the user
            UserProfile.objects.create(user=request.user, role='TEAM_MEMBER')
        
        response = self.get_response(request)
        return response