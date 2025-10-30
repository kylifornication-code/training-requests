from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*allowed_roles):
    """
    Decorator to restrict access based on user roles.
    Usage: @role_required('ADMIN', 'LEADERSHIP')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, 'Access denied: No user profile found.')
                return redirect('accounts:login')
            
            user_role = request.user.userprofile.role
            if user_role not in allowed_roles:
                messages.error(request, 'Access denied: Insufficient permissions.')
                raise PermissionDenied("You don't have permission to access this page.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def leadership_required(view_func):
    """Decorator to restrict access to leadership and admin users only"""
    return role_required('LEADERSHIP', 'ADMIN')(view_func)


def admin_required(view_func):
    """Decorator to restrict access to admin users only"""
    return role_required('ADMIN')(view_func)


class RoleRequiredMixin:
    """
    Mixin for class-based views to restrict access based on user roles.
    Usage: class MyView(RoleRequiredMixin, View):
               allowed_roles = ['ADMIN', 'LEADERSHIP']
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not hasattr(request.user, 'userprofile'):
            messages.error(request, 'Access denied: No user profile found.')
            return redirect('accounts:login')
        
        user_role = request.user.userprofile.role
        if user_role not in self.allowed_roles:
            messages.error(request, 'Access denied: Insufficient permissions.')
            raise PermissionDenied("You don't have permission to access this page.")
        
        return super().dispatch(request, *args, **kwargs)


class LeadershipRequiredMixin(RoleRequiredMixin):
    """Mixin to restrict access to leadership and admin users only"""
    allowed_roles = ['LEADERSHIP', 'ADMIN']


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin to restrict access to admin users only"""
    allowed_roles = ['ADMIN']