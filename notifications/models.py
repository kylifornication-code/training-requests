from django.db import models
from training_requests.models import TrainingRequest


class NotificationLog(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('REQUEST_SUBMITTED', 'Request Submitted'),
        ('REQUEST_APPROVED', 'Request Approved'),
        ('REQUEST_DENIED', 'Request Denied'),
        ('REQUEST_COMPLETED', 'Request Completed'),
    ]
    
    request = models.ForeignKey(
        TrainingRequest, 
        on_delete=models.CASCADE,
        help_text="Training request this notification is about"
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPE_CHOICES,
        help_text="Type of notification sent"
    )
    recipients = models.JSONField(
        help_text="List of recipient emails or user IDs"
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(
        default=False,
        help_text="Whether the notification was sent successfully"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if notification failed"
    )
    webhook_url = models.URLField(
        blank=True,
        help_text="Microsoft Teams webhook URL used"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts made"
    )
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.get_notification_type_display()} - {self.request.title}"
    
    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        ordering = ['-sent_at']
