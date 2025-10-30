"""
Views for notifications management and testing.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from training_requests.models import TrainingRequest
from .services import TeamsNotificationService, send_teams_notification
from .models import NotificationLog


@staff_member_required
def test_teams_connection(request):
    """Test Microsoft Teams webhook connection."""
    service = TeamsNotificationService()
    result = service.test_connection()
    
    if result['success']:
        messages.success(request, f"Teams connection test successful: {result['message']}")
    else:
        messages.error(request, f"Teams connection test failed: {result['error']}")
    
    return redirect('admin:notifications_notificationlog_changelist')


@staff_member_required
@require_POST
def send_test_notification(request, request_id):
    """Send a test notification for a specific training request."""
    training_request = get_object_or_404(TrainingRequest, id=request_id)
    notification_type = request.POST.get('notification_type', 'REQUEST_SUBMITTED')
    
    success = send_teams_notification(training_request, notification_type)
    
    if success:
        messages.success(
            request, 
            f"Test notification sent successfully for request: {training_request.title}"
        )
    else:
        messages.error(
            request, 
            f"Failed to send test notification for request: {training_request.title}"
        )
    
    return redirect('admin:training_requests_trainingrequest_change', training_request.id)


@staff_member_required
def notification_dashboard(request):
    """Dashboard showing notification statistics and recent logs."""
    # Get recent notification logs
    recent_logs = NotificationLog.objects.select_related('request').order_by('-sent_at')[:20]
    
    # Get statistics
    total_notifications = NotificationLog.objects.count()
    successful_notifications = NotificationLog.objects.filter(success=True).count()
    failed_notifications = NotificationLog.objects.filter(success=False).count()
    
    success_rate = (successful_notifications / total_notifications * 100) if total_notifications > 0 else 0
    
    # Get notification type breakdown
    notification_types = NotificationLog.objects.values('notification_type').distinct()
    type_stats = []
    for nt in notification_types:
        type_name = nt['notification_type']
        total = NotificationLog.objects.filter(notification_type=type_name).count()
        successful = NotificationLog.objects.filter(
            notification_type=type_name, 
            success=True
        ).count()
        type_stats.append({
            'type': type_name,
            'total': total,
            'successful': successful,
            'success_rate': (successful / total * 100) if total > 0 else 0
        })
    
    context = {
        'recent_logs': recent_logs,
        'total_notifications': total_notifications,
        'successful_notifications': successful_notifications,
        'failed_notifications': failed_notifications,
        'success_rate': round(success_rate, 1),
        'type_stats': type_stats,
    }
    
    return render(request, 'admin/notifications/dashboard.html', context)


@csrf_exempt
def webhook_test_endpoint(request):
    """
    Test endpoint that can receive webhook calls for testing.
    This is useful for testing webhook functionality without Teams.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            return JsonResponse({
                'status': 'success',
                'message': 'Webhook received successfully',
                'data': data
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests are allowed'
    }, status=405)
