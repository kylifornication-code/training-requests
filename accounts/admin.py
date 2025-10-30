from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.html import format_html
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.http import HttpResponse
from django.template.response import TemplateResponse
from datetime import datetime, timedelta
import csv
from .models import UserProfile
from .forms import CustomUserCreationForm, CustomUserChangeForm, UserProfileForm


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_profile_status', 'get_last_login', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__role', 'userprofile__is_active', 'date_joined', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'userprofile__role')
    actions = ['activate_users', 'deactivate_users', 'make_team_members', 'make_leadership', 'make_admins', 'export_users_csv']
    list_per_page = 25
    date_hierarchy = 'date_joined'
    
    # Enhanced fieldsets for better organization
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('role', 'profile_active'),
            'classes': ('wide',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role', 'is_active'),
        }),
    )
    
    def get_role(self, obj):
        return obj.userprofile.get_role_display() if hasattr(obj, 'userprofile') else 'No Profile'
    get_role.short_description = 'Role'
    
    def get_profile_status(self, obj):
        if hasattr(obj, 'userprofile'):
            if obj.userprofile.is_active:
                return format_html('<span style="color: green;">●</span> Active')
            else:
                return format_html('<span style="color: red;">●</span> Inactive')
        return 'No Profile'
    get_profile_status.short_description = 'Profile Status'
    
    def get_last_login(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return 'Never'
    get_last_login.short_description = 'Last Login'
    
    def activate_users(self, request, queryset):
        """Bulk action to activate selected users"""
        updated = 0
        for user in queryset:
            if hasattr(user, 'userprofile'):
                user.userprofile.is_active = True
                user.userprofile.save()
                user.is_active = True
                user.save()
                updated += 1
        
        if updated:
            messages.success(request, f'Successfully activated {updated} user(s).')
        else:
            messages.warning(request, 'No users were activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Bulk action to deactivate selected users"""
        updated = 0
        current_user_in_selection = False
        
        for user in queryset:
            if user == request.user:
                current_user_in_selection = True
                continue
                
            if hasattr(user, 'userprofile'):
                user.userprofile.is_active = False
                user.userprofile.save()
                user.is_active = False
                user.save()
                updated += 1
        
        if current_user_in_selection:
            messages.warning(request, 'Cannot deactivate your own account.')
        
        if updated:
            messages.success(request, f'Successfully deactivated {updated} user(s).')
        elif not current_user_in_selection:
            messages.warning(request, 'No users were deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def make_team_members(self, request, queryset):
        """Bulk action to set selected users as team members"""
        updated = 0
        for user in queryset:
            if hasattr(user, 'userprofile'):
                user.userprofile.role = 'TEAM_MEMBER'
                user.userprofile.save()
                updated += 1
        
        if updated:
            messages.success(request, f'Successfully changed {updated} user(s) to Team Member role.')
        else:
            messages.warning(request, 'No users were updated.')
    make_team_members.short_description = "Set as Team Members"
    
    def make_leadership(self, request, queryset):
        """Bulk action to set selected users as leadership"""
        updated = 0
        for user in queryset:
            if hasattr(user, 'userprofile'):
                user.userprofile.role = 'LEADERSHIP'
                user.userprofile.save()
                updated += 1
        
        if updated:
            messages.success(request, f'Successfully changed {updated} user(s) to Leadership role.')
        else:
            messages.warning(request, 'No users were updated.')
    make_leadership.short_description = "Set as Leadership"
    
    def make_admins(self, request, queryset):
        """Bulk action to set selected users as administrators"""
        updated = 0
        for user in queryset:
            if hasattr(user, 'userprofile'):
                user.userprofile.role = 'ADMIN'
                user.userprofile.save()
                updated += 1
        
        if updated:
            messages.success(request, f'Successfully changed {updated} user(s) to Administrator role.')
        else:
            messages.warning(request, 'No users were updated.')
    make_admins.short_description = "Set as Administrators"
    
    def export_users_csv(self, request, queryset):
        """Export selected users to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'First Name', 'Last Name', 'Role', 'Active', 'Date Joined', 'Last Login'])
        
        for user in queryset:
            role = user.userprofile.get_role_display() if hasattr(user, 'userprofile') else 'No Profile'
            active = user.userprofile.is_active if hasattr(user, 'userprofile') else user.is_active
            last_login = user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
            
            writer.writerow([
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                role,
                'Yes' if active else 'No',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                last_login
            ])
        
        return response
    export_users_csv.short_description = "Export selected users to CSV"
    
    def get_urls(self):
        """Add custom admin URLs"""
        urls = super().get_urls()
        custom_urls = [
            path('statistics/', self.admin_site.admin_view(self.user_statistics_view), name='accounts_user_statistics'),
        ]
        return custom_urls + urls
    
    def user_statistics_view(self, request):
        """Custom admin view for user statistics"""
        # Get user statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        
        # Role distribution
        role_stats = UserProfile.objects.values('role').annotate(count=Count('role')).order_by('role')
        
        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_registrations = User.objects.filter(date_joined__gte=thirty_days_ago).count()
        
        # Recent logins (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_logins = User.objects.filter(last_login__gte=seven_days_ago).count()
        
        # Users without profiles
        users_without_profiles = User.objects.filter(userprofile__isnull=True).count()
        
        context = {
            'title': 'User Statistics',
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'role_stats': role_stats,
            'recent_registrations': recent_registrations,
            'recent_logins': recent_logins,
            'users_without_profiles': users_without_profiles,
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        
        return TemplateResponse(request, 'admin/accounts/user_statistics.html', context)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileForm
    list_display = ('user', 'get_user_full_name', 'get_user_email', 'role', 'is_active', 'get_user_last_login', 'created_at', 'updated_at')
    list_filter = ('role', 'is_active', 'created_at', 'updated_at', 'user__is_staff', 'user__date_joined')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'get_user_info')
    actions = ['activate_profiles', 'deactivate_profiles', 'set_team_member_role', 'set_leadership_role', 'set_admin_role', 'export_profiles_csv']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'get_user_info'),
            'classes': ('wide',),
        }),
        ('Profile Settings', {
            'fields': ('role', 'is_active'),
            'classes': ('wide',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    get_user_full_name.short_description = 'Full Name'
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    
    def get_user_last_login(self, obj):
        if obj.user.last_login:
            return obj.user.last_login.strftime('%Y-%m-%d %H:%M')
        return 'Never'
    get_user_last_login.short_description = 'Last Login'
    
    def get_user_info(self, obj):
        """Display comprehensive user information"""
        info = f"""
        <strong>Username:</strong> {obj.user.username}<br>
        <strong>Email:</strong> {obj.user.email}<br>
        <strong>Full Name:</strong> {obj.user.first_name} {obj.user.last_name}<br>
        <strong>Staff Status:</strong> {'Yes' if obj.user.is_staff else 'No'}<br>
        <strong>Superuser:</strong> {'Yes' if obj.user.is_superuser else 'No'}<br>
        <strong>Date Joined:</strong> {obj.user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>Last Login:</strong> {obj.user.last_login.strftime('%Y-%m-%d %H:%M:%S') if obj.user.last_login else 'Never'}
        """
        return mark_safe(info)
    get_user_info.short_description = 'User Details'
    
    def activate_profiles(self, request, queryset):
        """Bulk action to activate selected user profiles"""
        updated = queryset.update(is_active=True)
        # Also update Django User is_active field
        for profile in queryset:
            profile.user.is_active = True
            profile.user.save()
        
        messages.success(request, f'Successfully activated {updated} user profile(s).')
    activate_profiles.short_description = "Activate selected profiles"
    
    def deactivate_profiles(self, request, queryset):
        """Bulk action to deactivate selected user profiles"""
        # Prevent deactivating current user
        current_user_profile = None
        if hasattr(request.user, 'userprofile'):
            current_user_profile = request.user.userprofile
        
        if current_user_profile and current_user_profile in queryset:
            messages.warning(request, 'Cannot deactivate your own profile.')
            queryset = queryset.exclude(id=current_user_profile.id)
        
        updated = queryset.update(is_active=False)
        # Also update Django User is_active field
        for profile in queryset:
            profile.user.is_active = False
            profile.user.save()
        
        if updated:
            messages.success(request, f'Successfully deactivated {updated} user profile(s).')
    deactivate_profiles.short_description = "Deactivate selected profiles"
    
    def set_team_member_role(self, request, queryset):
        """Bulk action to set role as team member"""
        updated = queryset.update(role='TEAM_MEMBER')
        messages.success(request, f'Successfully changed {updated} user(s) to Team Member role.')
    set_team_member_role.short_description = "Set role to Team Member"
    
    def set_leadership_role(self, request, queryset):
        """Bulk action to set role as leadership"""
        updated = queryset.update(role='LEADERSHIP')
        messages.success(request, f'Successfully changed {updated} user(s) to Leadership role.')
    set_leadership_role.short_description = "Set role to Leadership"
    
    def set_admin_role(self, request, queryset):
        """Bulk action to set role as administrator"""
        updated = queryset.update(role='ADMIN')
        messages.success(request, f'Successfully changed {updated} user(s) to Administrator role.')
    set_admin_role.short_description = "Set role to Administrator"
    
    def export_profiles_csv(self, request, queryset):
        """Export selected user profiles to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_profiles_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Full Name', 'Role', 'Profile Active', 'User Active', 'Created', 'Last Login'])
        
        for profile in queryset:
            full_name = f"{profile.user.first_name} {profile.user.last_name}".strip() or profile.user.username
            last_login = profile.user.last_login.strftime('%Y-%m-%d %H:%M:%S') if profile.user.last_login else 'Never'
            
            writer.writerow([
                profile.user.username,
                profile.user.email,
                full_name,
                profile.get_role_display(),
                'Yes' if profile.is_active else 'No',
                'Yes' if profile.user.is_active else 'No',
                profile.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                last_login
            ])
        
        return response
    export_profiles_csv.short_description = "Export selected profiles to CSV"
    
    def changelist_view(self, request, extra_context=None):
        """Add extra context to changelist view"""
        extra_context = extra_context or {}
        
        # Add profile statistics
        extra_context['active_profiles_count'] = UserProfile.objects.filter(is_active=True).count()
        extra_context['leadership_count'] = UserProfile.objects.filter(role__in=['LEADERSHIP', 'ADMIN']).count()
        
        return super().changelist_view(request, extra_context=extra_context)


# Custom admin site configuration
class CustomAdminSite(admin.AdminSite):
    site_header = 'Training Request Management System'
    site_title = 'Training Admin'
    index_title = 'Administration Dashboard'
    
    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request)
        
        # Sort the apps and models
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
        
        # Customize the order for better UX
        app_order = ['Accounts', 'Training_Requests', 'Notifications', 'Reports']
        ordered_apps = []
        
        for app_name in app_order:
            for app in app_list:
                if app['name'].replace(' ', '_').lower() == app_name.lower():
                    ordered_apps.append(app)
                    break
        
        # Add any remaining apps
        for app in app_list:
            if app not in ordered_apps:
                ordered_apps.append(app)
        
        return ordered_apps


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Also register with custom admin site
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(UserProfile, UserProfileAdmin)

# Customize admin site headers
admin.site.site_header = 'Training Request Management System'
admin.site.site_title = 'Training Admin'
admin.site.index_title = 'Administration Dashboard'

# Override admin index view to provide statistics
original_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    """Custom admin index view with statistics"""
    from training_requests.models import TrainingRequest
    
    extra_context = extra_context or {}
    
    # Add statistics to context
    extra_context.update({
        'total_users': User.objects.count(),
        'total_requests': TrainingRequest.objects.count(),
        'pending_requests': TrainingRequest.objects.filter(status='PENDING').count(),
    })
    
    return original_index(request, extra_context=extra_context)

# Replace the admin index view
admin.site.index = custom_admin_index
