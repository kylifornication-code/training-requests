"""
Microsoft Teams notification service for training request management system.
"""
import json
import logging
import time
from typing import Dict, List, Optional
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from accounts.models import UserProfile
from training_requests.models import TrainingRequest
from .models import NotificationLog
from .templates import NotificationTemplates


logger = logging.getLogger(__name__)


class TeamsNotificationService:
    """Service class for sending notifications to Microsoft Teams."""
    
    # Default webhook URL - should be configured in settings
    DEFAULT_WEBHOOK_URL = getattr(settings, 'TEAMS_WEBHOOK_URL', '')
    
    # Retry configuration
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 1
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize the Teams notification service.
        
        Args:
            webhook_url: Microsoft Teams webhook URL. If not provided, uses settings.
        """
        self.webhook_url = webhook_url or self.DEFAULT_WEBHOOK_URL
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            status_forcelist=self.RETRY_STATUS_CODES,
            backoff_factor=self.BACKOFF_FACTOR,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_leadership_recipients(self) -> List[str]:
        """
        Get list of leadership team members who should receive notifications.
        
        Returns:
            List of email addresses for leadership team members.
        """
        leadership_users = User.objects.filter(
            userprofile__role__in=['LEADERSHIP', 'ADMIN'],
            userprofile__is_active=True,
            is_active=True
        ).values_list('email', flat=True)
        
        # Filter out empty emails
        return [email for email in leadership_users if email]
    
    def create_card_payload(self, request: TrainingRequest, notification_type: str) -> Dict:
        """
        Create Microsoft Teams adaptive card payload for the notification.
        
        Args:
            request: TrainingRequest instance
            notification_type: Type of notification (REQUEST_SUBMITTED, etc.)
            
        Returns:
            Dictionary containing the Teams message payload
        """
        return NotificationTemplates.get_template(notification_type, request)
    
    def send_notification(self, request: TrainingRequest, notification_type: str) -> bool:
        """
        Send notification to Microsoft Teams.
        
        Args:
            request: TrainingRequest instance
            notification_type: Type of notification
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.error("Teams webhook URL not configured")
            return False
        
        recipients = self.get_leadership_recipients()
        if not recipients:
            logger.warning("No leadership recipients found for notification")
            return False
        
        # Create the notification log entry
        notification_log = NotificationLog.objects.create(
            request=request,
            notification_type=notification_type,
            recipients=recipients,
            webhook_url=self.webhook_url,
            success=False
        )
        
        try:
            # Create the Teams card payload
            payload = self.create_card_payload(request, notification_type)
            
            # Send the notification with retry logic
            success = self._send_with_retry(payload, notification_log)
            
            # Update the log entry
            notification_log.success = success
            notification_log.save()
            
            if success:
                logger.info(f"Teams notification sent successfully for request {request.id}")
            else:
                logger.error(f"Failed to send Teams notification for request {request.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending Teams notification: {str(e)}")
            notification_log.error_message = str(e)
            notification_log.save()
            return False
    
    def _send_with_retry(self, payload: Dict, notification_log: NotificationLog) -> bool:
        """
        Send notification with retry logic.
        
        Args:
            payload: Teams message payload
            notification_log: NotificationLog instance to update
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=30,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    return True
                elif response.status_code == 429:
                    # Rate limited - wait before retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                else:
                    logger.warning(f"Teams API returned status {response.status_code}: {response.text}")
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed on attempt {attempt + 1}: {str(e)}")
                
                if attempt < self.MAX_RETRIES:
                    # Exponential backoff
                    wait_time = self.BACKOFF_FACTOR * (2 ** attempt)
                    time.sleep(wait_time)
            
            # Update retry count
            notification_log.retry_count = attempt + 1
            notification_log.error_message = f"Failed after {attempt + 1} attempts"
            notification_log.save()
        
        return False
    
    def test_connection(self) -> Dict[str, any]:
        """
        Test the Teams webhook connection.
        
        Returns:
            Dictionary with test results
        """
        if not self.webhook_url:
            return {
                'success': False,
                'error': 'No webhook URL configured'
            }
        
        test_payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "Training System Test",
            "themeColor": "0078D4",
            "sections": [
                {
                    "activityTitle": "🧪 Training System Test Notification",
                    "activitySubtitle": "This is a test message from the Training Request Management System",
                    "text": "If you can see this message, the Microsoft Teams integration is working correctly."
                }
            ]
        }
        
        try:
            response = self.session.post(
                self.webhook_url,
                json=test_payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Test notification sent successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)}'
            }


# Convenience function for easy access
def send_teams_notification(request: TrainingRequest, notification_type: str) -> bool:
    """
    Convenience function to send Teams notification.
    
    Args:
        request: TrainingRequest instance
        notification_type: Type of notification
        
    Returns:
        True if successful, False otherwise
    """
    service = TeamsNotificationService()
    return service.send_notification(request, notification_type)