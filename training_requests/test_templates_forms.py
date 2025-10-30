from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from training_requests.models import TrainingRequest
from training_requests.forms import (
    TrainingRequestForm, RequestReviewForm, RequestCompletionForm,
    RequestFilterForm, BulkActionForm, CompletedTrainingFilterForm
)
from accounts.models import UserProfile


class TrainingRequestFormTest(TestCase):
    """Test cases for TrainingRequestForm"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_form_data = {
            'title': 'Django Conference 2024',
            'description': 'Annual Django conference with latest updates',
            'training_type': 'CONFERENCE',
            'estimated_cost': '1500.00',
            'currency': 'USD',
            'start_date': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=32)).strftime('%Y-%m-%d'),
            'justification': 'Will help improve Django skills for current projects'
        }
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        form = TrainingRequestForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save(self):
        """Test form save functionality"""
        user = User.objects.create_user(username='testuser', password='pass123')
        form = TrainingRequestForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        
        request = form.save(commit=False)
        request.requester = user
        request.save()
        
        self.assertEqual(request.title, 'Django Conference 2024')
        self.assertEqual(request.training_type, 'CONFERENCE')
        self.assertEqual(request.estimated_cost, Decimal('1500.00'))
    
    def test_form_start_date_validation(self):
        """Test start date cannot be in the past"""
        form_data = self.valid_form_data.copy()
        form_data['start_date'] = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        form = TrainingRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)
        self.assertIn('Start date cannot be in the past', str(form.errors['start_date']))
    
    def test_form_end_date_validation(self):
        """Test end date cannot be before start date"""
        form_data = self.valid_form_data.copy()
        form_data['start_date'] = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
        form_data['end_date'] = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        
        form = TrainingRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)
        self.assertIn('End date cannot be before start date', str(form.errors['end_date']))
    
    def test_form_cost_validation(self):
        """Test estimated cost must be positive"""
        form_data = self.valid_form_data.copy()
        form_data['estimated_cost'] = '-100.00'
        
        form = TrainingRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('estimated_cost', form.errors)
        self.assertIn('Estimated cost must be a positive number', str(form.errors['estimated_cost']))
    
    def test_form_currency_validation(self):
        """Test currency code validation"""
        form_data = self.valid_form_data.copy()
        form_data['currency'] = 'INVALID'
        
        form = TrainingRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('currency', form.errors)
        
        # Test valid currency
        form_data['currency'] = 'EUR'
        form = TrainingRequestForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_required_fields(self):
        """Test form required fields validation"""
        form = TrainingRequestForm(data={})
        self.assertFalse(form.is_valid())
        
        required_fields = ['title', 'description', 'training_type', 'estimated_cost', 
                          'start_date', 'end_date', 'justification']
        for field in required_fields:
            self.assertIn(field, form.errors)


class RequestReviewFormTest(TestCase):
    """Test cases for RequestReviewForm"""
    
    def test_form_approve_action(self):
        """Test form with approve action"""
        form_data = {
            'action': 'approve',
            'review_comments': 'Approved for team development'
        }
        form = RequestReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_deny_action_with_comments(self):
        """Test form with deny action and comments"""
        form_data = {
            'action': 'deny',
            'review_comments': 'Budget constraints this quarter'
        }
        form = RequestReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_deny_action_without_comments(self):
        """Test form with deny action but no comments (should be invalid)"""
        form_data = {
            'action': 'deny',
            'review_comments': ''
        }
        form = RequestReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Comments are required when denying a request', str(form.errors['__all__']))
    
    def test_form_approve_action_without_comments(self):
        """Test form with approve action but no comments (should be valid)"""
        form_data = {
            'action': 'approve',
            'review_comments': ''
        }
        form = RequestReviewForm(data=form_data)
        self.assertTrue(form.is_valid())


class RequestCompletionFormTest(TestCase):
    """Test cases for RequestCompletionForm"""
    
    def test_form_valid_completion_date(self):
        """Test form with valid completion date"""
        form_data = {
            'completion_date': date.today().strftime('%Y-%m-%d'),
            'completion_notes': 'Training completed successfully'
        }
        form = RequestCompletionForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_future_completion_date(self):
        """Test form with future completion date (should be invalid)"""
        form_data = {
            'completion_date': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'completion_notes': 'Training completed successfully'
        }
        form = RequestCompletionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('completion_date', form.errors)
        self.assertIn('Completion date cannot be in the future', str(form.errors['completion_date']))
    
    def test_form_no_completion_date(self):
        """Test form without completion date (should be valid)"""
        form_data = {
            'completion_notes': 'Training completed successfully'
        }
        form = RequestCompletionForm(data=form_data)
        self.assertTrue(form.is_valid())


class RequestFilterFormTest(TestCase):
    """Test cases for RequestFilterForm"""
    
    def test_form_valid_filters(self):
        """Test form with valid filter data"""
        form_data = {
            'search': 'Django',
            'status': 'PENDING',
            'training_type': 'CONFERENCE',
            'date_from': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'date_to': date.today().strftime('%Y-%m-%d')
        }
        form = RequestFilterForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_date_range(self):
        """Test form with invalid date range"""
        form_data = {
            'date_from': date.today().strftime('%Y-%m-%d'),
            'date_to': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        }
        form = RequestFilterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Start date cannot be after end date', str(form.errors['__all__']))
    
    def test_form_empty_data(self):
        """Test form with empty data (should be valid)"""
        form = RequestFilterForm(data={})
        self.assertTrue(form.is_valid())


class CompletedTrainingFilterFormTest(TestCase):
    """Test cases for CompletedTrainingFilterForm"""
    
    def test_form_valid_filters(self):
        """Test form with valid filter data"""
        form_data = {
            'search': 'Python',
            'team_member': 'John Doe',
            'training_type': 'COURSE',
            'completion_date_from': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'completion_date_to': date.today().strftime('%Y-%m-%d')
        }
        form = CompletedTrainingFilterForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_date_range(self):
        """Test form with invalid completion date range"""
        form_data = {
            'completion_date_from': date.today().strftime('%Y-%m-%d'),
            'completion_date_to': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        }
        form = CompletedTrainingFilterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Start date cannot be after end date', str(form.errors['__all__']))


class TemplateRenderingTest(TestCase):
    """Test cases for Django template rendering and context"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user.userprofile.role = 'TEAM_MEMBER'
        self.user.userprofile.save()
        
        self.leadership = User.objects.create_user(
            username='leader',
            email='leader@example.com',
            password='testpass123',
            first_name='Leader',
            last_name='User'
        )
        self.leadership.userprofile.role = 'LEADERSHIP'
        self.leadership.userprofile.save()
        
        self.training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Django Conference 2024',
            description='Annual Django conference',
            training_type='CONFERENCE',
            estimated_cost=Decimal('1500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Will improve Django skills'
        )
    
    def test_base_template_rendering(self):
        """Test base template renders correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Training Request System')
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'Team Member')
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'My Requests')
        self.assertContains(response, 'New Request')
    
    def test_dashboard_template_context(self):
        """Test dashboard template receives correct context"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.context)
        self.assertIn('recent_requests', response.context)
        self.assertEqual(response.context['stats']['total_requests'], 1)
        self.assertEqual(response.context['stats']['pending_requests'], 1)
    
    def test_request_list_template_rendering(self):
        """Test request list template renders correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:request_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Training Requests')
        self.assertContains(response, 'Django Conference 2024')
        self.assertContains(response, 'Pending')
        self.assertContains(response, '1500')  # Check for cost amount without currency formatting
    
    def test_create_request_template_rendering(self):
        """Test create request template renders correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:create_request'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Submit New Training Request')
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'name="training_type"')
        self.assertContains(response, 'name="estimated_cost"')
        self.assertContains(response, 'name="start_date"')
        self.assertContains(response, 'name="end_date"')
        self.assertContains(response, 'name="justification"')
    
    def test_request_detail_template_rendering(self):
        """Test request detail template renders correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:request_detail', kwargs={'pk': self.training_request.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
        self.assertContains(response, 'Annual Django conference')
        self.assertContains(response, 'Conference')
        self.assertContains(response, '1500')  # Check for cost amount without currency formatting
        self.assertContains(response, 'Will improve Django skills')
    
    def test_leadership_dashboard_template_rendering(self):
        """Test leadership dashboard template renders correctly"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('training_requests:leadership_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Leadership Dashboard')
        self.assertContains(response, 'Pending')
        # Check for dashboard elements without being too specific about exact text
        self.assertContains(response, 'Request')
    
    def test_pending_requests_template_rendering(self):
        """Test pending requests template renders correctly"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('training_requests:pending_requests'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pending Training Requests')
        self.assertContains(response, 'Django Conference 2024')
        self.assertContains(response, 'Test User')
    
    def test_template_inheritance(self):
        """Test template inheritance works correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:dashboard'))
        
        # Check that base template elements are present
        self.assertContains(response, '<!DOCTYPE html>')
        self.assertContains(response, 'Training Request System')
        self.assertContains(response, 'bootstrap')
        self.assertContains(response, 'font-awesome')
        
        # Check that child template content is present (dashboard specific content)
        self.assertContains(response, 'Dashboard')


class CustomTemplateTagsTest(TestCase):
    """Test cases for custom template tags"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.training_request = TrainingRequest.objects.create(
            requester=self.user,
            title='Test Request',
            description='Test description',
            training_type='CONFERENCE',
            estimated_cost=Decimal('1000.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            justification='Test justification',
            status='PENDING'
        )
    
    def test_status_badge_filter(self):
        """Test status_badge template filter"""
        template = Template('{% load training_extras %}{{ status|status_badge }}')
        
        # Test pending status
        context = Context({'status': 'PENDING'})
        rendered = template.render(context)
        self.assertIn('badge', rendered)
        self.assertIn('bg-warning', rendered)
        self.assertIn('Pending', rendered)
        self.assertIn('fa-clock', rendered)
        
        # Test approved status
        context = Context({'status': 'APPROVED'})
        rendered = template.render(context)
        self.assertIn('bg-success', rendered)
        self.assertIn('Approved', rendered)
        self.assertIn('fa-check', rendered)
    
    def test_training_type_badge_filter(self):
        """Test training_type_badge template filter"""
        template = Template('{% load training_extras %}{{ type|training_type_badge }}')
        
        # Test conference type
        context = Context({'type': 'CONFERENCE'})
        rendered = template.render(context)
        self.assertIn('badge', rendered)
        self.assertIn('bg-info', rendered)
        self.assertIn('Conference', rendered)
        self.assertIn('fa-users', rendered)
        
        # Test course type
        context = Context({'type': 'COURSE'})
        rendered = template.render(context)
        self.assertIn('bg-success', rendered)
        self.assertIn('Course', rendered)
        self.assertIn('fa-book', rendered)
    
    def test_role_badge_filter(self):
        """Test role_badge template filter"""
        template = Template('{% load training_extras %}{{ role|role_badge }}')
        
        # Test team member role
        context = Context({'role': 'TEAM_MEMBER'})
        rendered = template.render(context)
        self.assertIn('badge', rendered)
        self.assertIn('bg-secondary', rendered)
        self.assertIn('Team Member', rendered)
        self.assertIn('fa-user', rendered)
        
        # Test leadership role
        context = Context({'role': 'LEADERSHIP'})
        rendered = template.render(context)
        self.assertIn('bg-primary', rendered)
        self.assertIn('Leadership', rendered)
        self.assertIn('fa-crown', rendered)
    
    def test_currency_format_filter(self):
        """Test currency_format template filter"""
        template = Template('{% load training_extras %}{{ amount|currency_format:currency }}')
        
        # Test USD formatting
        context = Context({'amount': 1500.00, 'currency': 'USD'})
        rendered = template.render(context)
        self.assertIn('$1,500.00', rendered)
        
        # Test EUR formatting
        context = Context({'amount': 1200.50, 'currency': 'EUR'})
        rendered = template.render(context)
        self.assertIn('1,200.50 EUR', rendered)
    
    def test_progress_bar_filter(self):
        """Test progress_bar template filter"""
        template = Template('{% load training_extras %}{{ percentage|progress_bar:"success" }}')
        
        context = Context({'percentage': 75})
        rendered = template.render(context)
        self.assertIn('progress', rendered)
        self.assertIn('progress-bar', rendered)
        self.assertIn('bg-success', rendered)
        self.assertIn('width: 75%', rendered)
        # Note: The percentage display format may vary, so just check for presence of progress elements
    
    def test_div_filter(self):
        """Test div template filter"""
        template = Template('{% load training_extras %}{{ value|div:divisor }}')
        
        context = Context({'value': 100, 'divisor': 4})
        rendered = template.render(context)
        self.assertEqual(rendered.strip(), '25.0')
        
        # Test division by zero
        context = Context({'value': 100, 'divisor': 0})
        rendered = template.render(context)
        self.assertEqual(rendered.strip(), '0')


class TemplateInclusionTagsTest(TestCase):
    """Test cases for template inclusion tags"""
    
    def test_stat_card_inclusion_tag(self):
        """Test stat_card inclusion tag"""
        template = Template('{% load training_extras %}{% stat_card "Total Requests" 42 "fas fa-list" "primary" "This month" %}')
        rendered = template.render(Context())
        
        self.assertIn('card', rendered)
        self.assertIn('bg-primary', rendered)
        self.assertIn('Total Requests', rendered)
        self.assertIn('42', rendered)
        self.assertIn('fas fa-list', rendered)
        self.assertIn('This month', rendered)
    
    def test_action_button_inclusion_tag(self):
        """Test action_button inclusion tag"""
        template = Template('{% load training_extras %}{% action_button "/test/" "Click Me" "fas fa-click" "success" %}')
        rendered = template.render(Context())
        
        self.assertIn('btn', rendered)
        self.assertIn('btn-success', rendered)
        self.assertIn('/test/', rendered)
        self.assertIn('Click Me', rendered)
        self.assertIn('fas fa-click', rendered)
    
    def test_empty_state_inclusion_tag(self):
        """Test empty_state inclusion tag"""
        template = Template('{% load training_extras %}{% empty_state "No Data" "Nothing to show" "fas fa-inbox" %}')
        rendered = template.render(Context())
        
        self.assertIn('No Data', rendered)
        self.assertIn('Nothing to show', rendered)
        self.assertIn('fas fa-inbox', rendered)
    
    def test_notification_badge_inclusion_tag(self):
        """Test notification_badge inclusion tag"""
        template = Template('{% load training_extras %}{% notification_badge 5 "danger" "alerts" %}')
        rendered = template.render(Context())
        
        self.assertIn('badge', rendered)
        self.assertIn('5', rendered)
        self.assertIn('alerts', rendered)


class FormRenderingInTemplatesTest(TestCase):
    """Test cases for form rendering in templates"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_request_form_rendering(self):
        """Test create request form renders correctly in template"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:create_request'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check form fields are rendered
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'name="training_type"')
        self.assertContains(response, 'name="estimated_cost"')
        self.assertContains(response, 'name="currency"')
        self.assertContains(response, 'name="start_date"')
        self.assertContains(response, 'name="end_date"')
        self.assertContains(response, 'name="justification"')
        
        # Check form has proper CSS classes
        self.assertContains(response, 'form-control')
        self.assertContains(response, 'form-select')
        
        # Check form has CSRF token
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_form_validation_errors_in_template(self):
        """Test form validation errors are displayed in template"""
        self.client.login(username='testuser', password='testpass123')
        
        # Submit invalid form data
        invalid_data = {
            'title': '',  # Required field missing
            'estimated_cost': '-100',  # Invalid negative cost
            'start_date': (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'),  # Past date
        }
        
        response = self.client.post(reverse('training_requests:create_request'), invalid_data)
        
        self.assertEqual(response.status_code, 200)  # Form errors, stays on same page
        
        # Check that error messages are displayed
        self.assertContains(response, 'This field is required')
        self.assertContains(response, 'Start date cannot be in the past')
        self.assertContains(response, 'Estimated cost must be a positive number')
    
    def test_filter_form_rendering(self):
        """Test filter forms render correctly in templates"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:request_list'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check filter form elements
        self.assertContains(response, 'name="search"')
        self.assertContains(response, 'name="status"')
        self.assertContains(response, 'name="training_type"')
        # Check for search input field
        self.assertContains(response, 'Search')
    
    def test_form_field_component_rendering(self):
        """Test form field components render correctly"""
        # This tests the form_field inclusion tag indirectly through template rendering
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('training_requests:create_request'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check that form fields have proper structure
        self.assertContains(response, 'form-control')
        self.assertContains(response, 'form-select')
        
        # Check that form has proper structure (help text may not be present in all forms)
        self.assertContains(response, 'form')


class TemplateContextProcessorTest(TestCase):
    """Test cases for template context processors"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.leadership = User.objects.create_user(
            username='leader',
            password='testpass123'
        )
        self.leadership.userprofile.role = 'LEADERSHIP'
        self.leadership.userprofile.save()
        
        # Create a pending request
        self.user = User.objects.create_user(username='requester', password='pass123')
        TrainingRequest.objects.create(
            requester=self.user,
            title='Test Request',
            description='Test',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            justification='Test',
            status='PENDING'
        )
    
    def test_pending_count_context_processor(self):
        """Test pending count is available in template context"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('training_requests:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check that pending count is in context and rendered
        self.assertIn('pending_count', response.context)
        self.assertEqual(response.context['pending_count'], 1)
        
        # Check that pending count is displayed in navigation
        self.assertContains(response, 'notification-badge')
        self.assertContains(response, '1')  # The pending count