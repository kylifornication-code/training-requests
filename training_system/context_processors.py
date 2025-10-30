"""
Context processors for the training system application.
"""
from django.conf import settings
from training_requests.models import TrainingRequest


def global_context(request):
    """
    Add global context variables available to all templates.
    
    Args:
        request: Django request object
        
    Returns:
        dict: Context variables
    """
    context = {
        'site_name': 'Training Request System',
        'debug': settings.DEBUG,
    }
    
    # Add user-specific context for authenticated users
    if request.user.is_authenticated:
        user_role = getattr(request.user.userprofile, 'role', 'TEAM_MEMBER') if hasattr(request.user, 'userprofile') else 'TEAM_MEMBER'
        context['user_role'] = user_role
        
        # Add pending request count for leadership
        if user_role in ['LEADERSHIP', 'ADMIN']:
            pending_count = TrainingRequest.objects.filter(status='PENDING').count()
            context['pending_requests_count'] = pending_count
    
    return context