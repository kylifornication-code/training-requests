"""
Django signals for automatic Teams notifications on training request changes.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from training_requests.models import TrainingRequest
from .services import send_teams_notification


logger = logging.getLogger(__name__)


@receiver(pre_save, sender=TrainingRequest)
def capture_previous_status(sender, instance, **kwargs):
    """
    Capture the previous status before saving to detect status changes.
    """
    if instance.pk:
        try:
            previous = TrainingRequest.objects.get(pk=instance.pk)
            instance._previous_status = previous.status
        except TrainingRequest.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=TrainingRequest)
def send_training_request_notification(sender, instance, created, **kwargs):
    """
    Send Teams notification when training request is created or status changes.
    
    Args:
        sender: The model class (TrainingRequest)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    try:
        notification_type = None
        
        if created:
            # New request submitted
            notification_type = 'REQUEST_SUBMITTED'
            logger.info(f"New training request submitted: {instance.id}")
            
        else:
            # Check for status changes
            previous_status = getattr(instance, '_previous_status', None)
            current_status = instance.status
            
            if previous_status and previous_status != current_status:
                if current_status == 'APPROVED':
                    notification_type = 'REQUEST_APPROVED'
                    # Set reviewed_at timestamp if not already set
                    if not instance.reviewed_at:
                        instance.reviewed_at = timezone.now()
                        # Save without triggering signals again
                        TrainingRequest.objects.filter(pk=instance.pk).update(
                            reviewed_at=instance.reviewed_at
                        )
                    logger.info(f"Training request approved: {instance.id}")
                    
                elif current_status == 'DENIED':
                    notification_type = 'REQUEST_DENIED'
                    # Set reviewed_at timestamp if not already set
                    if not instance.reviewed_at:
                        instance.reviewed_at = timezone.now()
                        # Save without triggering signals again
                        TrainingRequest.objects.filter(pk=instance.pk).update(
                            reviewed_at=instance.reviewed_at
                        )
                    logger.info(f"Training request denied: {instance.id}")
                    
                elif current_status == 'COMPLETED':
                    notification_type = 'REQUEST_COMPLETED'
                    # Set completed_at timestamp if not already set
                    if not instance.completed_at:
                        instance.completed_at = timezone.now()
                        # Save without triggering signals again
                        TrainingRequest.objects.filter(pk=instance.pk).update(
                            completed_at=instance.completed_at
                        )
                    logger.info(f"Training request completed: {instance.id}")
        
        # Send notification if we have a type
        if notification_type:
            try:
                success = send_teams_notification(instance, notification_type)
                if success:
                    logger.info(f"Teams notification sent for request {instance.id}: {notification_type}")
                else:
                    logger.warning(f"Failed to send Teams notification for request {instance.id}: {notification_type}")
            except Exception as e:
                logger.error(f"Error sending Teams notification for request {instance.id}: {str(e)}")
                # Don't raise the exception to avoid breaking the save operation
        
    except Exception as e:
        logger.error(f"Error in training request notification signal: {str(e)}")
        # Don't raise the exception to avoid breaking the save operation


# Additional signal for manual notification triggering
def send_manual_notification(request_id: int, notification_type: str) -> bool:
    """
    Manually send a Teams notification for a specific request.
    
    Args:
        request_id: ID of the training request
        notification_type: Type of notification to send
        
    Returns:
        True if successful, False otherwise
    """
    try:
        request = TrainingRequest.objects.get(id=request_id)
        return send_teams_notification(request, notification_type)
    except TrainingRequest.DoesNotExist:
        logger.error(f"Training request {request_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending manual notification: {str(e)}")
        return False