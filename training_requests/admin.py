from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import TrainingRequest


@admin.register(TrainingRequest)
class TrainingRequestAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'requester', 
        'training_type', 
        'status_badge', 
        'estimated_cost', 
        'currency',
        'start_date', 
        'created_at'
    )
    list_filter = (
        'status', 
        'training_type', 
        'currency',
        'created_at', 
        'start_date'
    )
    search_fields = (
        'title', 
        'description', 
        'requester__username', 
        'requester__email',
        'requester__first_name',
        'requester__last_name'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Request Information', {
            'fields': ('requester', 'title', 'description', 'training_type')
        }),
        ('Cost and Dates', {
            'fields': ('estimated_cost', 'currency', 'start_date', 'end_date')
        }),
        ('Justification', {
            'fields': ('justification',)
        }),
        ('Review Information', {
            'fields': ('status', 'reviewer', 'review_comments', 'reviewed_at')
        }),
        ('Completion Information', {
            'fields': ('completed_at', 'completion_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_badge(self, obj):
        colors = {
            'PENDING': '#ffc107',
            'APPROVED': '#28a745', 
            'DENIED': '#dc3545',
            'COMPLETED': '#17a2b8'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['approve_requests', 'deny_requests', 'send_test_notification']
    
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            reviewer=request.user
        )
        self.message_user(request, f'{updated} requests were approved.')
    approve_requests.short_description = "Approve selected pending requests"
    
    def deny_requests(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='DENIED',
            reviewer=request.user
        )
        self.message_user(request, f'{updated} requests were denied.')
    deny_requests.short_description = "Deny selected pending requests"
    
    def send_test_notification(self, request, queryset):
        """Send test notifications for selected requests."""
        from notifications.services import send_teams_notification
        
        success_count = 0
        for training_request in queryset:
            try:
                # Send notification based on current status
                notification_type_map = {
                    'PENDING': 'REQUEST_SUBMITTED',
                    'APPROVED': 'REQUEST_APPROVED',
                    'DENIED': 'REQUEST_DENIED',
                    'COMPLETED': 'REQUEST_COMPLETED'
                }
                notification_type = notification_type_map.get(training_request.status, 'REQUEST_SUBMITTED')
                
                if send_teams_notification(training_request, notification_type):
                    success_count += 1
            except Exception as e:
                pass  # Error will be logged by the service
        
        total_count = queryset.count()
        if success_count == total_count:
            messages.success(request, f'Test notifications sent successfully for all {total_count} requests.')
        else:
            messages.warning(
                request, 
                f'Test notifications sent for {success_count} out of {total_count} requests. Check notification logs for details.'
            )
    send_test_notification.short_description = "Send test Teams notifications"
