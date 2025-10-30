from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.views.generic import CreateView, ListView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, UserRoleForm
from .decorators import role_required, AdminRequiredMixin, LeadershipRequiredMixin
from .models import UserProfile


class RegisterView(CreateView):
    """Custom user registration view with role assignment"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user if self.request.user.is_authenticated else None
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class UserListView(LeadershipRequiredMixin, ListView):
    """View for displaying team members - accessible to leadership and admin"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        """Get all users with their profiles, ordered by username"""
        return User.objects.select_related('userprofile').filter(
            userprofile__is_active=True
        ).order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = self.get_queryset().count()
        context['can_manage_users'] = self.request.user.userprofile.can_manage_users()
        return context


class UserCreateView(AdminRequiredMixin, CreateView):
    """View for creating new team members - admin only"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_create.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'User {form.instance.username} created successfully with role {form.instance.userprofile.get_role_display()}.'
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class UserRoleUpdateView(AdminRequiredMixin, UpdateView):
    """View for updating user roles - admin only"""
    model = UserProfile
    form_class = UserRoleForm
    template_name = 'accounts/user_role_update.html'
    success_url = reverse_lazy('accounts:user_list')

    def get_object(self):
        """Get UserProfile by user ID"""
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        return user.userprofile

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Role updated successfully for {form.instance.user.username} to {form.instance.get_role_display()}.'
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_user'] = self.object.user
        return context


@require_POST
@login_required
@role_required('ADMIN')
def toggle_user_status(request, user_id):
    """AJAX view to toggle user active status - admin only"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent admin from deactivating themselves
    if user == request.user:
        return JsonResponse({
            'success': False,
            'error': 'You cannot deactivate your own account.'
        })
    
    # Toggle the active status
    user.userprofile.is_active = not user.userprofile.is_active
    user.userprofile.save()
    
    # Also update Django's is_active field for consistency
    user.is_active = user.userprofile.is_active
    user.save()
    
    action = 'activated' if user.userprofile.is_active else 'deactivated'
    
    return JsonResponse({
        'success': True,
        'message': f'User {user.username} has been {action}.',
        'is_active': user.userprofile.is_active
    })
