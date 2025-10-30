from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import date, timedelta
import json
import requests

from training_requests.models import TrainingRequest
from notifications.models import NotificationLog
from notifications.services import TeamsNotificationService, send_teams_notification
from notifications.templates import NotificationTemplates
from notifications.signals import send_training_request_notification, capture_previous_status
from accounts.models import UserProfile


class NotificationLogModelTest(TestCase):
    """Test cases for NotificationLog model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        self.valid_notification_data = {
            'request': self.training_request,
            'notification_type': 'REQUEST_SUBMITTED',
            'recipients': ['leader1@example.com', 'leader2@example.com'],
            'success': True,
            'webhook_url': 'https://outlook.office.com/webhook/test'
        }
    
    def test_notification_log_creation(self):
        """Test basic NotificationLog creation"""
        notification = NotificationLog.objects.create(**self.valid_notification_data)
        
        self.assertEqual(notification.request, self.training_request)
        self.assertEqual(notification.notification_type, 'REQUEST_SUBMITTED')
        self.assertEqual(notification.recipients, ['leader1@example.com', 'leader2@example.com'])
        self.assertTrue(notification.success)
        self.assertIsNotNone(notification.sent_at)
    
    def test_notification_log_default_values(self):
        """Test NotificationLog default field values"""
        minimal_data = {
            'request': self.training_request,
            'notification_type': 'REQUEST_SUBMITTED',
            'recipients': ['test@example.com']
        }
        
        notification = NotificationLog.objects.create(**minimal_data)
        
        self.assertFalse(notification.success)  # Default False
        self.assertEqual(notification.error_message, '')  # Default empty
        self.assertEqual(notification.webhook_url, '')  # Default empty
        self.assertEqual(notification.retry_count, 0)  # Default 0
    
    def test_notification_type_choices(self):
        """Test NotificationLog notification_type field choices"""
        valid_types = [
            'REQUEST_SUBMITTED',
            'REQUEST_APPROVED', 
            'REQUEST_DENIED',
            'REQUEST_COMPLETED'
        ]
        
        for notification_type in valid_types:
            data = self.valid_notification_data.copy()
            data['notification_type'] = notification_type
            notification = NotificationLog.objects.create(**data)
            self.assertEqual(notification.notification_type, notification_type)
    
    def test_notification_log_str_method(self):
        """Test NotificationLog string representation"""
        # Test successful notification
        notification = NotificationLog.objects.create(**self.valid_notification_data)
        expected_str = "✓ Request Submitted - Test Training"
        self.assertEqual(str(notification), expected_str)
        
        # Test failed notification
        failed_data = self.valid_notification_data.copy()
        failed_data['success'] = False
        failed_notification = NotificationLog.objects.create(**failed_data)
        expected_str = "✗ Request Submitted - Test Training"
        self.assertEqual(str(failed_notification), expected_str)
    
    def test_foreign_key_relationship(self):
        """Test NotificationLog foreign key relationship with TrainingRequest"""
        notification = NotificationLog.objects.create(**self.valid_notification_data)
        
        self.assertEqual(notification.request, self.training_request)
        
        # Test reverse relationship
        notifications = self.training_request.notificationlog_set.all()
        self.assertIn(notification, notifications)
    
    def test_cascade_delete(self):
        """Test that NotificationLog is deleted when TrainingRequest is deleted"""
        notification = NotificationLog.objects.create(**self.valid_notification_data)
        notification_id = notification.id
        
        self.training_request.delete()
        
        # Notification should be deleted due to CASCADE
        with self.assertRaises(NotificationLog.DoesNotExist):
            NotificationLog.objects.get(id=notification_id)
    
    def test_json_field_recipients(self):
        """Test NotificationLog recipients JSONField functionality"""
        # Test with list of emails
        email_recipients = ['user1@example.com', 'user2@example.com']
        data = self.valid_notification_data.copy()
        data['recipients'] = email_recipients
        
        notification = NotificationLog.objects.create(**data)
        self.assertEqual(notification.recipients, email_recipients)
        
        # Test with list of user IDs
        user_id_recipients = [1, 2, 3]
        data['recipients'] = user_id_recipients
        notification2 = NotificationLog.objects.create(**data)
        self.assertEqual(notification2.recipients, user_id_recipients)
        
        # Test with mixed data
        mixed_recipients = ['user@example.com', 123, 'another@example.com']
        data['recipients'] = mixed_recipients
        notification3 = NotificationLog.objects.create(**data)
        self.assertEqual(notification3.recipients, mixed_recipients)
    
    def test_error_handling_fields(self):
        """Test NotificationLog error handling fields"""
        error_data = self.valid_notification_data.copy()
        error_data.update({
            'success': False,
            'error_message': 'Webhook URL returned 404 error',
            'retry_count': 3
        })
        
        notification = NotificationLog.objects.create(**error_data)
        
        self.assertFalse(notification.success)
        self.assertEqual(notification.error_message, 'Webhook URL returned 404 error')
        self.assertEqual(notification.retry_count, 3)
    
    def test_model_ordering(self):
        """Test NotificationLog model ordering"""
        # Create multiple notifications
        notification1 = NotificationLog.objects.create(**self.valid_notification_data)
        
        data2 = self.valid_notification_data.copy()
        data2['notification_type'] = 'REQUEST_APPROVED'
        notification2 = NotificationLog.objects.create(**data2)
        
        # Should be ordered by -sent_at (newest first)
        notifications = list(NotificationLog.objects.all())
        self.assertEqual(notifications[0], notification2)  # Newest first
        self.assertEqual(notifications[1], notification1)
    
    def test_webhook_url_field(self):
        """Test NotificationLog webhook_url field"""
        valid_urls = [
            'https://outlook.office.com/webhook/test',
            'https://hooks.slack.com/services/test',
            'http://localhost:8000/webhook'
        ]
        
        for url in valid_urls:
            data = self.valid_notification_data.copy()
            data['webhook_url'] = url
            notification = NotificationLog.objects.create(**data)
            self.assertEqual(notification.webhook_url, url)


class TeamsNotificationServiceTest(TestCase):
    """Test cases for TeamsNotificationService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create leadership users
        self.leader1 = User.objects.create_user(
            username='leader1',
            email='leader1@example.com',
            password='testpass123'
        )
        # Update the automatically created profile
        self.leader1.userprofile.role = 'LEADERSHIP'
        self.leader1.userprofile.save()
        
        self.leader2 = User.objects.create_user(
            username='leader2',
            email='leader2@example.com',
            password='testpass123'
        )
        # Update the automatically created profile
        self.leader2.userprofile.role = 'ADMIN'
        self.leader2.userprofile.save()
        
        self.training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        self.webhook_url = 'https://outlook.office.com/webhook/test'
        self.service = TeamsNotificationService(webhook_url=self.webhook_url)
    
    def test_service_initialization(self):
        """Test TeamsNotificationService initialization"""
        # Test with webhook URL
        service = TeamsNotificationService(webhook_url=self.webhook_url)
        self.assertEqual(service.webhook_url, self.webhook_url)
        
        # Test without webhook URL (should use default from settings)
        with override_settings(TEAMS_WEBHOOK_URL='https://default.webhook.url'):
            # Need to reload the module to pick up new settings
            from notifications.services import TeamsNotificationService as NewService
            service = NewService()
            self.assertEqual(service.webhook_url, 'https://default.webhook.url')
    
    def test_get_leadership_recipients(self):
        """Test getting leadership recipients"""
        recipients = self.service.get_leadership_recipients()
        
        self.assertIn('leader1@example.com', recipients)
        self.assertIn('leader2@example.com', recipients)
        self.assertNotIn('test@example.com', recipients)  # Regular user
        self.assertEqual(len(recipients), 2)
    
    def test_get_leadership_recipients_no_leaders(self):
        """Test getting leadership recipients when no leaders exist"""
        # Remove leadership roles
        UserProfile.objects.filter(role__in=['LEADERSHIP', 'ADMIN']).delete()
        
        recipients = self.service.get_leadership_recipients()
        self.assertEqual(recipients, [])
    
    def test_create_card_payload(self):
        """Test creating Teams card payload"""
        payload = self.service.create_card_payload(self.training_request, 'REQUEST_SUBMITTED')
        
        self.assertIn('@type', payload)
        self.assertEqual(payload['@type'], 'MessageCard')
        self.assertIn('sections', payload)
        self.assertIn('summary', payload)
        self.assertIn('Test Training', payload['summary'])
    
    @patch('notifications.services.requests.Session.post')
    def test_send_notification_success(self, mock_post):
        """Test successful notification sending"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = self.service.send_notification(self.training_request, 'REQUEST_SUBMITTED')
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Check notification log was created
        log = NotificationLog.objects.get(request=self.training_request)
        self.assertTrue(log.success)
        self.assertEqual(log.notification_type, 'REQUEST_SUBMITTED')
    
    @patch('notifications.services.requests.Session.post')
    def test_send_notification_failure(self, mock_post):
        """Test notification sending failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_post.return_value = mock_response
        
        result = self.service.send_notification(self.training_request, 'REQUEST_SUBMITTED')
        
        self.assertFalse(result)
        
        # Check notification log was created with failure
        log = NotificationLog.objects.get(request=self.training_request)
        self.assertFalse(log.success)
        self.assertIn('Failed after', log.error_message)
    
    def test_send_notification_no_webhook_url(self):
        """Test notification sending without webhook URL"""
        service = TeamsNotificationService(webhook_url='')
        
        result = service.send_notification(self.training_request, 'REQUEST_SUBMITTED')
        
        self.assertFalse(result)
    
    def test_send_notification_no_recipients(self):
        """Test notification sending with no leadership recipients"""
        # Remove all leadership users
        UserProfile.objects.filter(role__in=['LEADERSHIP', 'ADMIN']).delete()
        
        result = self.service.send_notification(self.training_request, 'REQUEST_SUBMITTED')
        
        self.assertFalse(result)
    
    @patch('notifications.services.requests.Session.post')
    def test_send_notification_with_retry(self, mock_post):
        """Test notification sending with retry logic"""
        # Mock responses: first two fail, third succeeds
        responses = [
            Mock(status_code=500, text='Server Error'),
            Mock(status_code=502, text='Bad Gateway'),
            Mock(status_code=200)
        ]
        mock_post.side_effect = responses
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.service.send_notification(self.training_request, 'REQUEST_SUBMITTED')
        
        self.assertTrue(result)
        self.assertEqual(mock_post.call_count, 3)
        
        # Check notification log shows retry count
        log = NotificationLog.objects.get(request=self.training_request)
        self.assertTrue(log.success)
        # The retry count reflects the attempt number when it succeeded (3rd attempt = count 3)
        # But the service updates count after each attempt, so successful on 3rd = count 3
        self.assertGreaterEqual(log.retry_count, 2)  # At least 2 retries before success
    
    @patch('notifications.services.requests.Session.post')
    def test_send_notification_rate_limited(self, mock_post):
        """Test notification sending with rate limiting"""
        # Mock rate limited response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '1'}
        mock_post.return_value = mock_response
        
        with patch('time.sleep') as mock_sleep:
            result = self.service.send_notification(self.training_request, 'REQUEST_SUBMITTED')
        
        self.assertFalse(result)
        mock_sleep.assert_called_with(1)  # Should respect Retry-After header
    
    @patch('notifications.services.requests.Session.post')
    def test_test_connection_success(self, mock_post):
        """Test successful connection test"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = self.service.test_connection()
        
        self.assertTrue(result['success'])
        self.assertIn('successfully', result['message'])
    
    @patch('notifications.services.requests.Session.post')
    def test_test_connection_failure(self, mock_post):
        """Test failed connection test"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_post.return_value = mock_response
        
        result = self.service.test_connection()
        
        self.assertFalse(result['success'])
        self.assertIn('HTTP 404', result['error'])
    
    def test_test_connection_no_webhook(self):
        """Test connection test without webhook URL"""
        service = TeamsNotificationService(webhook_url='')
        
        result = service.test_connection()
        
        self.assertFalse(result['success'])
        self.assertIn('No webhook URL', result['error'])


class NotificationTemplatesTest(TestCase):
    """Test cases for NotificationTemplates"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            first_name='Review',
            last_name='Manager',
            password='testpass123'
        )
        
        self.training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Advanced Python Training',
            description='Comprehensive Python training course',
            training_type='COURSE',
            estimated_cost=Decimal('1500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Need to improve Python skills for upcoming projects',
            reviewer=self.reviewer,
            review_comments='Approved for Q1 training budget'
        )
    
    @override_settings(BASE_URL='https://training.example.com')
    def test_get_base_url(self):
        """Test getting base URL from settings"""
        url = NotificationTemplates.get_base_url()
        self.assertEqual(url, 'https://training.example.com')
    
    def test_get_request_url(self):
        """Test generating request URL"""
        with override_settings(BASE_URL='https://training.example.com'):
            url = NotificationTemplates.get_request_url(self.training_request)
            expected_url = f'https://training.example.com/requests/{self.training_request.id}/'
            self.assertEqual(url, expected_url)
    
    def test_request_submitted_template(self):
        """Test request submitted template"""
        template = NotificationTemplates.request_submitted_template(self.training_request)
        
        self.assertEqual(template['@type'], 'MessageCard')
        self.assertIn('Advanced Python Training', template['summary'])
        self.assertEqual(template['themeColor'], '0078D4')
        
        # Check sections
        self.assertIn('sections', template)
        section = template['sections'][0]
        self.assertIn('New Training Request Submitted', section['activityTitle'])
        
        # Check facts
        facts = section['facts']
        fact_names = [fact['name'] for fact in facts]
        self.assertIn('Training Title:', fact_names)
        self.assertIn('Requester:', fact_names)
        self.assertIn('Estimated Cost:', fact_names)
        
        # Check action
        self.assertIn('potentialAction', template)
        action = template['potentialAction'][0]
        self.assertEqual(action['name'], 'Review Request')
    
    def test_request_approved_template(self):
        """Test request approved template"""
        template = NotificationTemplates.request_approved_template(self.training_request)
        
        self.assertEqual(template['@type'], 'MessageCard')
        self.assertIn('Training Request Approved', template['summary'])
        self.assertEqual(template['themeColor'], '107C10')  # Green
        
        section = template['sections'][0]
        self.assertIn('Training Request Approved', section['activityTitle'])
        
        # Check reviewer information is included
        facts = section['facts']
        approved_by_fact = next(fact for fact in facts if fact['name'] == 'Approved by:')
        self.assertEqual(approved_by_fact['value'], 'Review Manager')
    
    def test_request_denied_template(self):
        """Test request denied template"""
        template = NotificationTemplates.request_denied_template(self.training_request)
        
        self.assertEqual(template['@type'], 'MessageCard')
        self.assertIn('Training Request Denied', template['summary'])
        self.assertEqual(template['themeColor'], 'D13438')  # Red
        
        section = template['sections'][0]
        self.assertIn('Training Request Denied', section['activityTitle'])
        
        # Check denial reason is included
        self.assertIn('Reason for Denial', section['text'])
    
    def test_request_completed_template(self):
        """Test request completed template"""
        # Set completion data
        self.training_request.completed_at = timezone.now()
        self.training_request.completion_notes = 'Successfully completed the course'
        
        template = NotificationTemplates.request_completed_template(self.training_request)
        
        self.assertEqual(template['@type'], 'MessageCard')
        self.assertIn('Training Completed', template['summary'])
        self.assertEqual(template['themeColor'], '8764B8')  # Purple
        
        section = template['sections'][0]
        self.assertIn('Training Request Completed', section['activityTitle'])
        
        # Check completion information
        self.assertIn('Completion Notes', section['text'])
        self.assertIn('Successfully completed', section['text'])
    
    def test_get_template_valid_types(self):
        """Test getting templates for valid notification types"""
        valid_types = [
            'REQUEST_SUBMITTED',
            'REQUEST_APPROVED',
            'REQUEST_DENIED',
            'REQUEST_COMPLETED'
        ]
        
        for notification_type in valid_types:
            template = NotificationTemplates.get_template(notification_type, self.training_request)
            self.assertIsInstance(template, dict)
            self.assertEqual(template['@type'], 'MessageCard')
    
    def test_get_template_invalid_type(self):
        """Test getting template for invalid notification type"""
        template = NotificationTemplates.get_template('INVALID_TYPE', self.training_request)
        
        # Should fallback to submitted template
        self.assertIsInstance(template, dict)
        self.assertEqual(template['@type'], 'MessageCard')
        self.assertIn('New Training Request Submitted', template['sections'][0]['activityTitle'])
    
    def test_template_with_no_reviewer(self):
        """Test templates when no reviewer is set"""
        self.training_request.reviewer = None
        
        approved_template = NotificationTemplates.request_approved_template(self.training_request)
        section = approved_template['sections'][0]
        facts = section['facts']
        approved_by_fact = next(fact for fact in facts if fact['name'] == 'Approved by:')
        self.assertEqual(approved_by_fact['value'], 'Unknown')
    
    def test_template_with_long_justification(self):
        """Test template with long justification text"""
        long_justification = 'A' * 400  # Longer than 300 chars
        self.training_request.justification = long_justification
        
        template = NotificationTemplates.request_submitted_template(self.training_request)
        section = template['sections'][0]
        
        # Should be truncated with ellipsis
        self.assertIn('...', section['text'])
        self.assertTrue(len(section['text']) < len(long_justification))


class NotificationSignalsTest(TestCase):
    """Test cases for notification signals"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create leadership user
        self.leader = User.objects.create_user(
            username='leader',
            email='leader@example.com',
            password='testpass123'
        )
        # Update the automatically created profile
        self.leader.userprofile.role = 'LEADERSHIP'
        self.leader.userprofile.save()
    
    @patch('notifications.signals.send_teams_notification')
    def test_signal_on_request_creation(self, mock_send):
        """Test signal is triggered when new request is created"""
        mock_send.return_value = True
        
        # Create new training request
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        # Signal should have been called
        mock_send.assert_called_once_with(training_request, 'REQUEST_SUBMITTED')
    
    @patch('notifications.signals.send_teams_notification')
    def test_signal_on_status_change_to_approved(self, mock_send):
        """Test signal is triggered when request is approved"""
        mock_send.return_value = True
        
        # Create request
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        mock_send.reset_mock()  # Reset after creation
        
        # Change status to approved
        training_request.status = 'APPROVED'
        training_request.reviewer = self.leader
        training_request.save()
        
        # Signal should have been called for approval
        mock_send.assert_called_with(training_request, 'REQUEST_APPROVED')
    
    @patch('notifications.signals.send_teams_notification')
    def test_signal_on_status_change_to_denied(self, mock_send):
        """Test signal is triggered when request is denied"""
        mock_send.return_value = True
        
        # Create request
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        mock_send.reset_mock()  # Reset after creation
        
        # Change status to denied
        training_request.status = 'DENIED'
        training_request.reviewer = self.leader
        training_request.review_comments = 'Budget constraints'
        training_request.save()
        
        # Signal should have been called for denial
        mock_send.assert_called_with(training_request, 'REQUEST_DENIED')
    
    @patch('notifications.signals.send_teams_notification')
    def test_signal_on_status_change_to_completed(self, mock_send):
        """Test signal is triggered when request is completed"""
        mock_send.return_value = True
        
        # Create approved request
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification',
            status='APPROVED'
        )
        
        mock_send.reset_mock()  # Reset after creation
        
        # Change status to completed
        training_request.status = 'COMPLETED'
        training_request.completion_notes = 'Training completed successfully'
        training_request.save()
        
        # Signal should have been called for completion
        mock_send.assert_called_with(training_request, 'REQUEST_COMPLETED')
    
    @patch('notifications.signals.send_teams_notification')
    def test_signal_not_triggered_on_same_status(self, mock_send):
        """Test signal is not triggered when status doesn't change"""
        mock_send.return_value = True
        
        # Create request
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        mock_send.reset_mock()  # Reset after creation
        
        # Save without changing status
        training_request.description = 'Updated description'
        training_request.save()
        
        # Signal should not have been called
        mock_send.assert_not_called()
    
    def test_capture_previous_status_signal(self):
        """Test that previous status is captured correctly"""
        # Create request
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        # Change status
        training_request.status = 'APPROVED'
        training_request.save()
        
        # Previous status should have been captured
        self.assertEqual(training_request._previous_status, 'PENDING')
    
    @patch('notifications.signals.send_teams_notification')
    def test_signal_error_handling(self, mock_send):
        """Test signal error handling doesn't break save operation"""
        # Make send_teams_notification raise an exception
        mock_send.side_effect = Exception('Network error')
        
        # Create request - should not raise exception
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        # Request should still be created
        self.assertTrue(TrainingRequest.objects.filter(id=training_request.id).exists())


class NotificationIntegrationTest(TestCase):
    """Integration tests for the complete notification system"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.leader = User.objects.create_user(
            username='leader',
            email='leader@example.com',
            password='testpass123'
        )
        # Update the automatically created profile
        self.leader.userprofile.role = 'LEADERSHIP'
        self.leader.userprofile.save()
    
    @patch('notifications.services.requests.Session.post')
    @override_settings(TEAMS_WEBHOOK_URL='https://test.webhook.url')
    def test_end_to_end_notification_flow(self, mock_post):
        """Test complete notification flow from request creation to Teams"""
        # Mock successful Teams response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Create training request (should trigger notification)
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='End-to-End Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        # Verify Teams webhook was called
        mock_post.assert_called_once()
        
        # Verify notification log was created
        log = NotificationLog.objects.get(request=training_request)
        self.assertEqual(log.notification_type, 'REQUEST_SUBMITTED')
        self.assertTrue(log.success)
        self.assertIn('leader@example.com', log.recipients)
        
        # Verify the payload structure
        call_args = mock_post.call_args
        payload = call_args[1]['json']  # kwargs['json']
        self.assertEqual(payload['@type'], 'MessageCard')
        self.assertIn('End-to-End Test Training', payload['summary'])
    
    @patch('notifications.services.send_teams_notification')
    def test_convenience_function(self, mock_send):
        """Test the convenience function for sending notifications"""
        mock_send.return_value = True
        
        training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification'
        )
        
        # Use convenience function
        result = send_teams_notification(training_request, 'REQUEST_SUBMITTED')
        
        self.assertTrue(result)
        mock_send.assert_called_with(training_request, 'REQUEST_SUBMITTED')
