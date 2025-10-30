from django.contrib.auth.models import User
from .models import UserProfile


def admin_dashboard_stats(request):
    """
    Context processor to provide dashboard statistics for admin interface
    """
    if not request.path.startswith('/admin/'):
        return {}
    
    try:
        # Import here to avoid circular imports
        from training_requests.models import TrainingRequest
        
        stats = {
            'total_users': User.objects.count(),
            'total_requests': TrainingRequest.objects.count(),
            'pending_requests': TrainingRequest.objects.filter(status='PENDING').count(),
        }
    except ImportError:
        # If training_requests app is not available, provide basic stats
        stats = {
            'total_users': User.objects.count(),
            'total_requests': 0,
            'pending_requests': 0,
        }
    
    return stats