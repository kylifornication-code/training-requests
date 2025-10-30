from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from training_requests.models import TrainingRequest
from accounts.models import UserProfile


class TrainingRequestModelTest(TestCase):
    """Test cases for TrainingRequest model"""
    
    def setUp(self):
        """Set up test data"""
        self.requester = User.objects.create_user(
            username='requester',
            email='requester@example.com',
            password='testpass123'
        )
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123'
        )
        
        self.valid_request_data = {
            'requester': self.requester,
            'title': 'Django Conference 2024',
            'description': 'Annual Django conference with latest updates',
            'training_type': 'CONFERENCE',
            'estimated_cost': Decimal('1500.00'),
            'currency': 'USD',
            'start_date': date.today() + timedelta(days=30),
            'end_date': date.today() + timedelta(days=32),
            'justification': 'Will help improve Django skills for current projects'
        }
    
    def test_training_request_creation(self):
        """Test basic TrainingRequest creation"""
        request = TrainingRequest.objects.create(**self.valid_request_data)
        
        self.assertEqual(request.requester, self.requester)
        self.assertEqual(request.title, 'Django Conference 2024')
        self.assertEqual(request.status, 'PENDING')  # Default status
        self.assertIsNotNone(request.created_at)
        self.assertIsNotNone(request.updated_at)
    
    def test_training_request_default_values(self):
        """Test TrainingRequest default field values"""
        request = TrainingRequest.objects.create(**self.valid_request_data)
        
        self.assertEqual(request.status, 'PENDING')
        self.assertEqual(request.currency, 'USD')
        self.assertIsNone(request.reviewer)
        self.assertEqual(request.review_comments, '')
        self.assertIsNone(request.reviewed_at)
        self.assertIsNone(request.completed_at)
        self.assertEqual(request.completion_notes, '')
    
    def test_training_request_str_method(self):
        """Test TrainingRequest string representation"""
        request = TrainingRequest.objects.create(**self.valid_request_data)
        expected_str = f"Django Conference 2024 - requester (Pending)"
        self.assertEqual(str(request), expected_str)
    
    def test_training_type_choices(self):
        """Test TrainingRequest training_type field choices"""
        valid_types = ['CONFERENCE', 'COURSE', 'CERTIFICATION', 'WORKSHOP']
        
        for training_type in valid_types:
            data = self.valid_request_data.copy()
            data['training_type'] = training_type
            request = TrainingRequest.objects.create(**data)
            self.assertEqual(request.training_type, training_type)
    
    def test_status_choices(self):
        """Test TrainingRequest status field choices"""
        request = TrainingRequest.objects.create(**self.valid_request_data)
        valid_statuses = ['PENDING', 'APPROVED', 'DENIED', 'COMPLETED']
        
        for status in valid_statuses:
            request.status = status
            request.save()
            request.refresh_from_db()
            self.assertEqual(request.status, status)
    
    def test_status_transitions(self):
        """Test TrainingRequest status state transitions"""
        request = TrainingRequest.objects.create(**self.valid_request_data)
        
        # Test PENDING -> APPROVED
        self.assertEqual(request.status, 'PENDING')
        request.status = 'APPROVED'
        request.reviewer = self.reviewer
        request.save()
        self.assertEqual(request.status, 'APPROVED')
        
        # Test APPROVED -> COMPLETED
        request.status = 'COMPLETED'
        request.save()
        self.assertEqual(request.status, 'COMPLETED')
        
        # Test PENDING -> DENIED
        request2 = TrainingRequest.objects.create(**self.valid_request_data)
        request2.status = 'DENIED'
        request2.reviewer = self.reviewer
        request2.save()
        self.assertEqual(request2.status, 'DENIED')
    
    def test_date_validation(self):
        """Test TrainingRequest date validation"""
        # Test invalid date range (start_date > end_date)
        invalid_data = self.valid_request_data.copy()
        invalid_data['start_date'] = date.today() + timedelta(days=32)
        invalid_data['end_date'] = date.today() + timedelta(days=30)
        
        request = TrainingRequest(**invalid_data)
        with self.assertRaises(ValidationError):
            request.clean()
    
    def test_cost_validation(self):
        """Test TrainingRequest cost field validation"""
        # Test negative cost (should be prevented by validator)
        invalid_data = self.valid_request_data.copy()
        invalid_data['estimated_cost'] = Decimal('-100.00')
        
        request = TrainingRequest(**invalid_data)
        with self.assertRaises(ValidationError):
            request.full_clean()
    
    def test_foreign_key_relationships(self):
        """Test TrainingRequest foreign key relationships"""
        request = TrainingRequest.objects.create(**self.valid_request_data)
        
        # Test requester relationship
        self.assertEqual(request.requester, self.requester)
        self.assertIn(request, self.requester.training_requests.all())
        
        # Test reviewer relationship
        request.reviewer = self.reviewer
        request.save()
        self.assertEqual(request.reviewer, self.reviewer)
        self.assertIn(request, self.reviewer.reviewed_requests.all())
    
    def test_cascade_delete_requester(self):
        """Test that TrainingRequest is deleted when requester is deleted"""
        request = TrainingRequest.objects.create(**self.valid_request_data)
        request_id = request.id
        
        self.requester.delete()
        
        # Request should be deleted due to CASCADE
        with self.assertRaises(TrainingRequest.DoesNotExist):
            TrainingRequest.objects.get(id=request_id)
    
    def test_set_null_reviewer(self):
        """Test that reviewer is set to NULL when reviewer user is deleted"""
        request = TrainingRequest.objects.create(**self.valid_request_data)
        request.reviewer = self.reviewer
        request.save()
        
        self.reviewer.delete()
        request.refresh_from_db()
        
        # Reviewer should be set to NULL due to SET_NULL
        self.assertIsNone(request.reviewer)
    
    def test_decimal_precision(self):
        """Test TrainingRequest estimated_cost decimal precision"""
        data = self.valid_request_data.copy()
        data['estimated_cost'] = Decimal('1234567.89')
        
        request = TrainingRequest.objects.create(**data)
        self.assertEqual(request.estimated_cost, Decimal('1234567.89'))
    
    def test_model_ordering(self):
        """Test TrainingRequest model ordering"""
        # Create multiple requests
        request1 = TrainingRequest.objects.create(**self.valid_request_data)
        
        data2 = self.valid_request_data.copy()
        data2['title'] = 'Second Request'
        request2 = TrainingRequest.objects.create(**data2)
        
        # Should be ordered by -created_at (newest first)
        requests = list(TrainingRequest.objects.all())
        self.assertEqual(requests[0], request2)  # Newest first
        self.assertEqual(requests[1], request1)
    
    def test_required_fields(self):
        """Test TrainingRequest required fields"""
        from django.db import transaction
        
        # Test missing required fields - should raise IntegrityError
        with self.assertRaises((IntegrityError, ValueError)):
            with transaction.atomic():
                TrainingRequest.objects.create()
        
        # Test with minimal required fields
        minimal_data = {
            'requester': self.requester,
            'title': 'Test',
            'description': 'Test description',
            'training_type': 'COURSE',
            'estimated_cost': Decimal('100.00'),
            'start_date': date.today(),
            'end_date': date.today(),
            'justification': 'Test justification'
        }
        
        request = TrainingRequest.objects.create(**minimal_data)
        self.assertIsNotNone(request.id)


class TrainingRequestViewTest(TestCase):
    """Test cases for TrainingRequest views"""
    
    def setUp(self):
        """Set up test data for view tests"""
        self.client = Client()
        
        # Create test users with different roles
        self.team_member = User.objects.create_user(
            username='teammember',
            email='teammember@example.com',
            password='testpass123',
            first_name='Team',
            last_name='Member'
        )
        self.team_member_profile = UserProfile.objects.get(user=self.team_member)
        self.team_member_profile.role = 'TEAM_MEMBER'
        self.team_member_profile.save()
        
        self.leadership = User.objects.create_user(
            username='leadership',
            email='leadership@example.com',
            password='testpass123',
            first_name='Leader',
            last_name='Ship'
        )
        self.leadership_profile = UserProfile.objects.get(user=self.leadership)
        self.leadership_profile.role = 'LEADERSHIP'
        self.leadership_profile.save()
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User'
        )
        self.admin_profile = UserProfile.objects.get(user=self.admin)
        self.admin_profile.role = 'ADMIN'
        self.admin_profile.save()
        
        # Create test training request
        self.training_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Django Conference 2024',
            description='Annual Django conference with latest updates',
            training_type='CONFERENCE',
            estimated_cost=Decimal('1500.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Will help improve Django skills for current projects'
        )
    
    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated users"""
        self.client.login(username='teammember', password='testpass123')
        response = self.client.get(reverse('training_requests:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'teammember')
        self.assertContains(response, 'Team Member')
        
        # Test that dashboard shows user statistics
        self.assertContains(response, 'Total Requests')
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Approved')
        self.assertContains(response, 'Completed')
        
        # Test that dashboard shows recent requests section
        self.assertContains(response, 'Recent Training Requests')
        
        # Test that dashboard shows the user's training request
        self.assertContains(response, 'Django Conference 2024')
        
        # Test context data
        self.assertIn('stats', response.context)
        self.assertIn('recent_requests', response.context)
        self.assertEqual(response.context['stats']['total_requests'], 1)
        self.assertEqual(response.context['stats']['pending_requests'], 1)
    
    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view redirects unauthenticated users"""
        response = self.client.get(reverse('training_requests:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_view_filtering(self):
        """Test dashboard view with search and status filtering"""
        # Create additional training request
        TrainingRequest.objects.create(
            requester=self.team_member,
            title='Python Workshop',
            description='Python programming workshop',
            training_type='WORKSHOP',
            estimated_cost=Decimal('200.00'),
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=16),
            justification='Learn Python',
            status='APPROVED'
        )
        
        self.client.login(username='teammember', password='testpass123')
        
        # Test search filtering
        response = self.client.get(reverse('training_requests:dashboard'), {'search': 'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Workshop')
        self.assertNotContains(response, 'Django Conference 2024')
        
        # Test status filtering
        response = self.client.get(reverse('training_requests:dashboard'), {'status': 'APPROVED'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Workshop')
        self.assertNotContains(response, 'Django Conference 2024')
        
        # Test combined filtering
        response = self.client.get(reverse('training_requests:dashboard'), {
            'search': 'Django',
            'status': 'PENDING'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
        self.assertNotContains(response, 'Python Workshop')
    
    def test_create_request_view_get(self):
        """Test GET request to create training request view"""
        self.client.login(username='teammember', password='testpass123')
        response = self.client.get(reverse('training_requests:create_request'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Submit New Training Request')
        self.assertContains(response, 'form')
    
    def test_create_request_view_post_valid(self):
        """Test POST request with valid data to create training request"""
        self.client.login(username='teammember', password='testpass123')
        
        form_data = {
            'title': 'Python Workshop 2024',
            'description': 'Advanced Python programming workshop',
            'training_type': 'WORKSHOP',
            'estimated_cost': '800.00',
            'currency': 'USD',
            'start_date': (date.today() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=17)).strftime('%Y-%m-%d'),
            'justification': 'Will enhance Python skills for backend development'
        }
        
        response = self.client.post(reverse('training_requests:create_request'), form_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('training_requests:request_list'))
        
        # Verify request was created
        new_request = TrainingRequest.objects.get(title='Python Workshop 2024')
        self.assertEqual(new_request.requester, self.team_member)
        self.assertEqual(new_request.status, 'PENDING')
    
    def test_create_request_view_post_invalid(self):
        """Test POST request with invalid data to create training request"""
        self.client.login(username='teammember', password='testpass123')
        
        form_data = {
            'title': '',  # Missing required field
            'description': 'Test description',
            'training_type': 'WORKSHOP',
            'estimated_cost': '-100.00',  # Invalid negative cost
            'currency': 'USD',
            'start_date': (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'),  # Past date
            'end_date': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'justification': 'Test justification'
        }
        
        response = self.client.post(reverse('training_requests:create_request'), form_data)
        
        self.assertEqual(response.status_code, 200)  # Form errors, stays on same page
        self.assertContains(response, 'This field is required')
    
    def test_request_list_view_team_member(self):
        """Test request list view for team member (shows only own requests)"""
        # Create another request by different user
        other_user = User.objects.create_user(username='other', password='test')
        TrainingRequest.objects.create(
            requester=other_user,
            title='Other User Request',
            description='Test',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            justification='Test'
        )
        
        self.client.login(username='teammember', password='testpass123')
        response = self.client.get(reverse('training_requests:request_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
        self.assertNotContains(response, 'Other User Request')
        self.assertContains(response, 'My Training Requests')
    
    def test_request_list_view_leadership(self):
        """Test request list view for leadership (shows all requests)"""
        # Create another request by different user
        other_user = User.objects.create_user(username='other', password='test')
        TrainingRequest.objects.create(
            requester=other_user,
            title='Other User Request',
            description='Test',
            training_type='COURSE',
            estimated_cost=Decimal('500.00'),
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            justification='Test'
        )
        
        self.client.login(username='leadership', password='testpass123')
        response = self.client.get(reverse('training_requests:request_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
        self.assertContains(response, 'Other User Request')
        self.assertContains(response, 'All Training Requests')
    
    def test_request_list_view_filtering(self):
        """Test request list view with filtering parameters"""
        self.client.login(username='teammember', password='testpass123')
        
        # Test status filter
        response = self.client.get(reverse('training_requests:request_list'), {'status': 'PENDING'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
        
        # Test search filter
        response = self.client.get(reverse('training_requests:request_list'), {'search': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
        
        # Test training type filter
        response = self.client.get(reverse('training_requests:request_list'), {'training_type': 'CONFERENCE'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
    
    def test_request_list_view_pagination(self):
        """Test request list view pagination"""
        # Create multiple requests to test pagination
        for i in range(15):
            TrainingRequest.objects.create(
                requester=self.team_member,
                title=f'Test Request {i}',
                description='Test description',
                training_type='COURSE',
                estimated_cost=Decimal('100.00'),
                start_date=date.today() + timedelta(days=i+1),
                end_date=date.today() + timedelta(days=i+2),
                justification='Test justification'
            )
        
        self.client.login(username='teammember', password='testpass123')
        response = self.client.get(reverse('training_requests:request_list'))
        
        self.assertEqual(response.status_code, 200)
        # Should show 10 items per page (paginate_by = 10)
        self.assertEqual(len(response.context['requests']), 10)
        self.assertTrue(response.context['is_paginated'])
    
    def test_request_detail_view_owner(self):
        """Test request detail view for request owner"""
        self.client.login(username='teammember', password='testpass123')
        response = self.client.get(reverse('training_requests:request_detail', kwargs={'pk': self.training_request.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
        self.assertContains(response, 'Annual Django conference')
        self.assertEqual(response.context['request'], self.training_request)
    
    def test_request_detail_view_leadership(self):
        """Test request detail view for leadership"""
        self.client.login(username='leadership', password='testpass123')
        response = self.client.get(reverse('training_requests:request_detail', kwargs={'pk': self.training_request.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')
        self.assertTrue(response.context['can_approve'])
        self.assertFalse(response.context['can_complete'])
    
    def test_request_detail_view_unauthorized(self):
        """Test request detail view for unauthorized user (different team member)"""
        other_user = User.objects.create_user(username='other', password='test')
        self.client.login(username='other', password='test')
        
        response = self.client.get(reverse('training_requests:request_detail', kwargs={'pk': self.training_request.pk}))
        self.assertEqual(response.status_code, 404)
    
    def test_approve_request_view_leadership(self):
        """Test approve request view for leadership"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.post(
            reverse('training_requests:approve_request', kwargs={'pk': self.training_request.pk}),
            {'review_comments': 'Approved for team development'}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('training_requests:request_detail', kwargs={'pk': self.training_request.pk}))
        
        # Verify request was approved
        self.training_request.refresh_from_db()
        self.assertEqual(self.training_request.status, 'APPROVED')
        self.assertEqual(self.training_request.reviewer, self.leadership)
        self.assertEqual(self.training_request.review_comments, 'Approved for team development')
        self.assertIsNotNone(self.training_request.reviewed_at)
    
    def test_approve_request_view_team_member_forbidden(self):
        """Test approve request view forbidden for team member"""
        self.client.login(username='teammember', password='testpass123')
        
        response = self.client.post(
            reverse('training_requests:approve_request', kwargs={'pk': self.training_request.pk}),
            {'review_comments': 'Should not work'}
        )
        
        self.assertEqual(response.status_code, 403)
        
        # Verify request was not approved
        self.training_request.refresh_from_db()
        self.assertEqual(self.training_request.status, 'PENDING')
    
    def test_deny_request_view_leadership(self):
        """Test deny request view for leadership"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.post(
            reverse('training_requests:deny_request', kwargs={'pk': self.training_request.pk}),
            {'review_comments': 'Budget constraints this quarter'}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('training_requests:request_detail', kwargs={'pk': self.training_request.pk}))
        
        # Verify request was denied
        self.training_request.refresh_from_db()
        self.assertEqual(self.training_request.status, 'DENIED')
        self.assertEqual(self.training_request.reviewer, self.leadership)
        self.assertEqual(self.training_request.review_comments, 'Budget constraints this quarter')
        self.assertIsNotNone(self.training_request.reviewed_at)
    
    def test_deny_request_view_without_comments(self):
        """Test deny request view requires comments"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.post(
            reverse('training_requests:deny_request', kwargs={'pk': self.training_request.pk}),
            {'review_comments': ''}  # Empty comments
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify request was not denied due to missing comments
        self.training_request.refresh_from_db()
        self.assertEqual(self.training_request.status, 'PENDING')
    
    def test_complete_request_view_leadership(self):
        """Test complete request view for leadership"""
        # First approve the request
        self.training_request.status = 'APPROVED'
        self.training_request.save()
        
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.post(
            reverse('training_requests:complete_request', kwargs={'pk': self.training_request.pk}),
            {'completion_notes': 'Training completed successfully'}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('training_requests:request_detail', kwargs={'pk': self.training_request.pk}))
        
        # Verify request was completed
        self.training_request.refresh_from_db()
        self.assertEqual(self.training_request.status, 'COMPLETED')
        self.assertEqual(self.training_request.completion_notes, 'Training completed successfully')
        self.assertIsNotNone(self.training_request.completed_at)
    
    def test_complete_request_view_pending_request(self):
        """Test complete request view fails for pending request"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.post(
            reverse('training_requests:complete_request', kwargs={'pk': self.training_request.pk}),
            {'completion_notes': 'Should not work'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify request was not completed
        self.training_request.refresh_from_db()
        self.assertEqual(self.training_request.status, 'PENDING')
    
    def test_pending_requests_view_leadership(self):
        """Test pending requests view for leadership"""
        # Create additional pending and non-pending requests
        approved_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Approved Request',
            description='Test',
            training_type='COURSE',
            estimated_cost=Decimal('300.00'),
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=7),
            justification='Test',
            status='APPROVED'
        )
        
        self.client.login(username='leadership', password='testpass123')
        response = self.client.get(reverse('training_requests:pending_requests'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference 2024')  # Pending request
        self.assertNotContains(response, 'Approved Request')  # Non-pending request
        self.assertContains(response, 'Pending Training Requests')
    
    def test_pending_requests_view_team_member_forbidden(self):
        """Test pending requests view forbidden for team member"""
        self.client.login(username='teammember', password='testpass123')
        
        response = self.client.get(reverse('training_requests:pending_requests'))
        self.assertEqual(response.status_code, 403)
    
    def test_form_validation_in_views(self):
        """Test form validation in create request view"""
        self.client.login(username='teammember', password='testpass123')
        
        # Test invalid date range
        form_data = {
            'title': 'Test Request',
            'description': 'Test description',
            'training_type': 'WORKSHOP',
            'estimated_cost': '500.00',
            'currency': 'USD',
            'start_date': (date.today() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=5)).strftime('%Y-%m-%d'),  # End before start
            'justification': 'Test justification'
        }
        
        response = self.client.post(reverse('training_requests:create_request'), form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'End date cannot be before start date')
    
    def test_view_permissions_unauthenticated(self):
        """Test that all views require authentication"""
        views_to_test = [
            ('training_requests:dashboard', {}),
            ('training_requests:create_request', {}),
            ('training_requests:request_list', {}),
            ('training_requests:request_detail', {'pk': self.training_request.pk}),
            ('training_requests:pending_requests', {}),
        ]
        
        for view_name, kwargs in views_to_test:
            response = self.client.get(reverse(view_name, kwargs=kwargs))
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)
    
    def test_view_context_data(self):
        """Test that views provide correct context data"""
        self.client.login(username='leadership', password='testpass123')
        
        # Test request list view context
        response = self.client.get(reverse('training_requests:request_list'))
        self.assertEqual(response.context['user_role'], 'LEADERSHIP')
        self.assertTrue(response.context['is_leadership'])
        self.assertIn('status_choices', response.context)
        self.assertIn('training_type_choices', response.context)
        
        # Test request detail view context
        response = self.client.get(reverse('training_requests:request_detail', kwargs={'pk': self.training_request.pk}))
        self.assertTrue(response.context['can_approve'])
        self.assertFalse(response.context['can_complete'])  # Not approved yet


class TrainingCompletionTrackingTest(TestCase):
    """Test cases for training completion tracking functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.team_member = User.objects.create_user(
            username='team_member',
            email='team_member@example.com',
            password='testpass123'
        )
        self.leadership = User.objects.create_user(
            username='leadership',
            email='leadership@example.com',
            password='testpass123'
        )
        
        # Update user profiles (they are created automatically by signals)
        self.team_member.userprofile.role = 'TEAM_MEMBER'
        self.team_member.userprofile.save()
        self.leadership.userprofile.role = 'LEADERSHIP'
        self.leadership.userprofile.save()
        
        # Create approved training request
        self.approved_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Python Advanced Course',
            description='Advanced Python programming course',
            training_type='COURSE',
            estimated_cost=Decimal('800.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            justification='Improve Python skills',
            status='APPROVED',
            reviewer=self.leadership,
            reviewed_at=timezone.now()
        )
        
        # Create completed training request
        self.completed_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='React Workshop',
            description='React development workshop',
            training_type='WORKSHOP',
            estimated_cost=Decimal('500.00'),
            currency='USD',
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() - timedelta(days=3),
            justification='Learn React for frontend projects',
            status='COMPLETED',
            reviewer=self.leadership,
            reviewed_at=timezone.now() - timedelta(days=10),
            completed_at=timezone.now() - timedelta(days=2),
            completion_notes='Great workshop, learned a lot about React hooks'
        )
        
        self.client = Client()
    
    def test_complete_request_form_get(self):
        """Test GET request to complete training request form"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.get(
            reverse('training_requests:complete_request', kwargs={'pk': self.approved_request.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Complete Training Request')
        self.assertContains(response, self.approved_request.title)
        self.assertIn('form', response.context)
    
    def test_complete_request_form_post_valid(self):
        """Test POST request with valid completion data"""
        self.client.login(username='leadership', password='testpass123')
        
        completion_data = {
            'completion_date': date.today().strftime('%Y-%m-%d'),
            'completion_notes': 'Training completed successfully with excellent feedback'
        }
        
        response = self.client.post(
            reverse('training_requests:complete_request', kwargs={'pk': self.approved_request.pk}),
            data=completion_data
        )
        
        # Should redirect to request detail
        self.assertEqual(response.status_code, 302)
        
        # Check that request was marked as completed
        self.approved_request.refresh_from_db()
        self.assertEqual(self.approved_request.status, 'COMPLETED')
        self.assertIsNotNone(self.approved_request.completed_at)
        self.assertEqual(self.approved_request.completion_notes, completion_data['completion_notes'])
    
    def test_complete_request_form_post_no_date(self):
        """Test POST request without completion date (should default to today)"""
        self.client.login(username='leadership', password='testpass123')
        
        completion_data = {
            'completion_notes': 'Training completed successfully'
        }
        
        response = self.client.post(
            reverse('training_requests:complete_request', kwargs={'pk': self.approved_request.pk}),
            data=completion_data
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check that request was marked as completed with today's date
        self.approved_request.refresh_from_db()
        self.assertEqual(self.approved_request.status, 'COMPLETED')
        self.assertEqual(self.approved_request.completed_at.date(), date.today())
    
    def test_complete_request_pending_request_error(self):
        """Test that pending requests cannot be marked as completed"""
        pending_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Pending Course',
            description='A pending course',
            training_type='COURSE',
            estimated_cost=Decimal('300.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=22),
            justification='Learning new skills',
            status='PENDING'
        )
        
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.get(
            reverse('training_requests:complete_request', kwargs={'pk': pending_request.pk})
        )
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
    
    def test_training_statistics_view(self):
        """Test training statistics dashboard view"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.get(reverse('training_requests:training_statistics'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Training Statistics Dashboard')
        
        # Check context data
        self.assertIn('total_requests', response.context)
        self.assertIn('completed_count', response.context)
        self.assertIn('completion_rate', response.context)
        self.assertIn('total_investment', response.context)
        self.assertIn('type_breakdown', response.context)
        self.assertIn('top_learners', response.context)
    
    def test_completed_training_report_view(self):
        """Test completed training report view"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.get(reverse('training_requests:completed_training_report'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Completed Training Report')
        self.assertContains(response, self.completed_request.title)
        
        # Check context data
        self.assertIn('filter_form', response.context)
        self.assertIn('filtered_count', response.context)
        self.assertIn('filtered_total_cost', response.context)
    
    def test_completed_training_report_filtering(self):
        """Test completed training report with filters"""
        self.client.login(username='leadership', password='testpass123')
        
        # Test search filter
        response = self.client.get(
            reverse('training_requests:completed_training_report'),
            {'search': 'React'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.completed_request.title)
        
        # Test training type filter
        response = self.client.get(
            reverse('training_requests:completed_training_report'),
            {'training_type': 'WORKSHOP'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.completed_request.title)
    
    def test_export_completed_training_csv(self):
        """Test CSV export of completed training"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.get(reverse('training_requests:export_completed_training'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Request ID', content)  # Header
        self.assertIn(self.completed_request.title, content)  # Data
    
    def test_export_completed_training_csv_with_filters(self):
        """Test CSV export with filters applied"""
        self.client.login(username='leadership', password='testpass123')
        
        response = self.client.get(
            reverse('training_requests:export_completed_training'),
            {'training_type': 'WORKSHOP'}
        )
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn(self.completed_request.title, content)
    
    def test_completion_tracking_permissions(self):
        """Test that only leadership can access completion tracking features"""
        # Test team member access (should be forbidden)
        self.client.login(username='team_member', password='testpass123')
        
        views_to_test = [
            ('training_requests:complete_request', {'pk': self.approved_request.pk}),
            ('training_requests:training_statistics', {}),
            ('training_requests:completed_training_report', {}),
            ('training_requests:export_completed_training', {}),
        ]
        
        for view_name, kwargs in views_to_test:
            response = self.client.get(reverse(view_name, kwargs=kwargs))
            # Should be forbidden (403) or redirect (302) depending on the view
            self.assertIn(response.status_code, [302, 403])
    
    def test_completion_form_validation(self):
        """Test completion form validation"""
        from training_requests.forms import RequestCompletionForm
        
        # Test valid form
        form_data = {
            'completion_date': date.today().strftime('%Y-%m-%d'),
            'completion_notes': 'Training completed successfully'
        }
        form = RequestCompletionForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test future completion date (should be invalid)
        form_data = {
            'completion_date': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'completion_notes': 'Training completed successfully'
        }
        form = RequestCompletionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('completion_date', form.errors)
    
    def test_completed_training_filter_form_validation(self):
        """Test completed training filter form validation"""
        from training_requests.forms import CompletedTrainingFilterForm
        
        # Test valid form
        form_data = {
            'completion_date_from': (date.today() - timedelta(days=10)).strftime('%Y-%m-%d'),
            'completion_date_to': date.today().strftime('%Y-%m-%d'),
            'training_type': 'COURSE'
        }
        form = CompletedTrainingFilterForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test invalid date range (from > to)
        form_data = {
            'completion_date_from': date.today().strftime('%Y-%m-%d'),
            'completion_date_to': (date.today() - timedelta(days=10)).strftime('%Y-%m-%d'),
        }
        form = CompletedTrainingFilterForm(data=form_data)
        self.assertFalse(form.is_valid())