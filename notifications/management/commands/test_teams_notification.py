"""
Django management command for testing Microsoft Teams notifications.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

from training_requests.models import TrainingRequest
from notifications.services import TeamsNotificationService, send_teams_notification
from notifications.signals import send_manual_notification


class Command(BaseCommand):
    help = 'Test Microsoft Teams notification system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--webhook-url',
            type=str,
            help='Microsoft Teams webhook URL to test (overrides settings)'
        )
        
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Test webhook connection only'
        )
        
        parser.add_argument(
            '--request-id',
            type=int,
            help='Send notification for specific training request ID'
        )
        
        parser.add_argument(
            '--notification-type',
            type=str,
            choices=['REQUEST_SUBMITTED', 'REQUEST_APPROVED', 'REQUEST_DENIED', 'REQUEST_COMPLETED'],
            default='REQUEST_SUBMITTED',
            help='Type of notification to send'
        )
        
        parser.add_argument(
            '--create-test-request',
            action='store_true',
            help='Create a test training request and send notification'
        )
        
        parser.add_argument(
            '--list-recipients',
            action='store_true',
            help='List current leadership recipients'
        )
    
    def handle(self, *args, **options):
        """Handle the command execution."""
        
        # Initialize the service
        webhook_url = options.get('webhook_url')
        self._webhook_url = webhook_url  # Store for use in other methods
        service = TeamsNotificationService(webhook_url=webhook_url)
        
        if options['list_recipients']:
            self.list_recipients(service)
            return
        
        if options['test_connection']:
            self.test_connection(service)
            return
        
        if options['create_test_request']:
            self.create_and_test_request(service, options['notification_type'])
            return
        
        if options['request_id']:
            self.test_existing_request(options['request_id'], options['notification_type'])
            return
        
        # Default: show help
        self.stdout.write(
            self.style.WARNING(
                'No action specified. Use --help to see available options.'
            )
        )
    
    def list_recipients(self, service):
        """List current leadership recipients."""
        self.stdout.write("Current leadership recipients:")
        
        recipients = service.get_leadership_recipients()
        if recipients:
            for email in recipients:
                self.stdout.write(f"  - {email}")
            self.stdout.write(
                self.style.SUCCESS(f"Total: {len(recipients)} recipients")
            )
        else:
            self.stdout.write(
                self.style.WARNING("No leadership recipients found!")
            )
            self.stdout.write(
                "Make sure you have users with LEADERSHIP or ADMIN roles and valid email addresses."
            )
    
    def test_connection(self, service):
        """Test the webhook connection."""
        self.stdout.write("Testing Microsoft Teams webhook connection...")
        
        if not service.webhook_url:
            self.stdout.write(
                self.style.ERROR(
                    "No webhook URL configured. Set TEAMS_WEBHOOK_URL in settings or use --webhook-url"
                )
            )
            return
        
        self.stdout.write(f"Webhook URL: {service.webhook_url}")
        
        result = service.test_connection()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f"✓ {result['message']}")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"✗ {result['error']}")
            )
    
    def create_and_test_request(self, service, notification_type):
        """Create a test training request and send notification."""
        self.stdout.write("Creating test training request...")
        
        # Find or create a test user
        test_user, created = User.objects.get_or_create(
            username='test_requester',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            self.stdout.write(f"Created test user: {test_user.username}")
        
        # Create test training request
        request = TrainingRequest.objects.create(
            requester=test_user,
            title='Test Training Request',
            description='This is a test training request created by the management command.',
            training_type='COURSE',
            estimated_cost=1500.00,
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Testing the Microsoft Teams notification system integration.',
            status='PENDING'
        )
        
        self.stdout.write(f"Created test request ID: {request.id}")
        
        # Send notification
        self.stdout.write(f"Sending {notification_type} notification...")
        
        success = service.send_notification(request, notification_type)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS("✓ Notification sent successfully!")
            )
        else:
            self.stdout.write(
                self.style.ERROR("✗ Failed to send notification")
            )
        
        # Ask if user wants to delete the test request
        self.stdout.write(
            f"\nTest request created with ID {request.id}. "
            "You may want to delete it after testing."
        )
    
    def test_existing_request(self, request_id, notification_type):
        """Send notification for an existing training request."""
        try:
            request = TrainingRequest.objects.get(id=request_id)
            self.stdout.write(f"Found request: {request.title}")
            
            self.stdout.write(f"Sending {notification_type} notification...")
            
            # Use the service with the configured webhook URL
            webhook_url = getattr(self, '_webhook_url', None)
            service = TeamsNotificationService(webhook_url=webhook_url)
            success = service.send_notification(request, notification_type)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("✓ Notification sent successfully!")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("✗ Failed to send notification")
                )
                
        except TrainingRequest.DoesNotExist:
            raise CommandError(f"Training request with ID {request_id} not found")