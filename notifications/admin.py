from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from .models import NotificationLog
from .services import TeamsNotificationService, send_teams_notification


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        'success_icon',
        'notification_type',
        'request_title',
        'recipient_count',
        'retry_count',
        'sent_at'
    )
    list_filter = (
        'success',
        'notification_type',
        'sent_at',
        'retry_count'
    )
    search_fields = (
        'request__title',
        'request__requester__username',
        'error_message'
    )
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('request', 'notification_type', 'recipients')
        }),
        ('Delivery Information', {
            'fields': ('success', 'webhook_url', 'retry_count', 'sent_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )
    
    def success_icon(self, obj):
        if obj.success:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗</span>'
            )
    success_icon.short_description = 'Status'
    
    def request_title(self, obj):
        return obj.request.title
    request_title.short_description = 'Training Request'
    
    def recipient_count(self, obj):
        if isinstance(obj.recipients, list):
            return len(obj.recipients)
        return 0
    recipient_count.short_description = 'Recipients'
    
    actions = ['retry_failed_notifications', 'test_teams_connection']
    
    def retry_failed_notifications(self, request, queryset):
        """Retry failed notifications."""
        failed_notifications = queryset.filter(success=False)
        retry_count = 0
        
        for log in failed_notifications:
            try:
                success = send_teams_notification(log.request, log.notification_type)
                if success:
                    retry_count += 1
            except Exception as e:
                pass  # Error will be logged by the service
        
        self.message_user(
            request, 
            f'{retry_count} out of {failed_notifications.count()} notifications retried successfully.'
        )
    retry_failed_notifications.short_description = "Retry failed notifications"
    
    def test_teams_connection(self, request, queryset):
        """Test Microsoft Teams webhook connection."""
        service = TeamsNotificationService()
        result = service.test_connection()
        
        if result['success']:
            messages.success(request, f"Teams connection test successful: {result['message']}")
        else:
            messages.error(request, f"Teams connection test failed: {result['error']}")
        
        return redirect('admin:notifications_notificationlog_changelist')
    test_teams_connection.short_description = "Test Teams connection"
    
    def get_urls(self):
        """Add custom URLs for admin actions."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'test-connection/',
                self.admin_site.admin_view(self.test_connection_view),
                name='notifications_test_connection'
            ),
        ]
        return custom_urls + urls
    
    def test_connection_view(self, request):
        """Custom view for testing Teams connection."""
        service = TeamsNotificationService()
        result = service.test_connection()
        
        if result['success']:
            messages.success(request, f"✓ Teams connection successful: {result['message']}")
        else:
            messages.error(request, f"✗ Teams connection failed: {result['error']}")
        
        return redirect('admin:notifications_notificationlog_changelist')
