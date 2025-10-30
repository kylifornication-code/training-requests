from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from training_requests.models import TrainingRequest
from accounts.models import UserProfile


class TrainingRequestWorkflowIntegrationTest(TestCase):
    """Integration tests for complete training request workflows"""
    
    def setUp(self):
        """Set up test data for integration tests"""
        self.client = Client()
        
        # Create users with different roles
        self.team_member = User.objects.create_user(
            username='teammember',
            email='teammember@example.com',
            password='testpass123',
            first_name='Team',
            last_name='Member'
        )
        self.team_member.userprofile.role = 'TEAM_MEMBER'
        self.team_member.userprofile.save()
        
        self.leadership = User.objects.create_user(
            username='leadership',
            email='leadership@example.com',
            password='testpass123',
            first_name='Leader',
            last_name='Ship'
        )
        self.leadership.userprofile.role = 'LEADERSHIP'
        self.leadership.userprofile.save()
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )
        self.admin.userprofile.role = 'ADMIN'
        self.admin.userprofile.save()
        
        # Create a test training request for workflow testing
        self.training_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Django Advanced Workshop',
            description='Advanced Django development workshop covering best practices',
            training_type='WORKSHOP',
            estimated_cost=Decimal('1200.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Will improve Django skills for current and future projects',
            status='PENDING'
        )
    
    def test_complete_request_submission_to_approval_workflow(self):
        """Test complete workflow from request submission to approval"""
        # Step 1: Team member logs in and views their existing request
        self.client.login(username='teammember', password='testpass123')
        
        # Navigate to dashboard
        dashboard_response = self.client.get('/dashboard/')
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, 'Team Member')
        
        # Step 2: Team member views their request in the list
        request_list_response = self.client.get('/requests/')
        self.assertEqual(request_list_response.status_code, 200)
        self.assertContains(request_list_response, 'Django Advanced Workshop')
        self.assertContains(request_list_response, 'Pending')
        
        # View request details
        detail_response = self.client.get(f'/requests/{self.training_request.pk}/')
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Django Advanced Workshop')
        self.assertContains(detail_response, 'Advanced Django development workshop')
        
        # Step 3: Leadership logs in and reviews pending requests
        self.client.logout()
        self.client.login(username='leadership', password='testpass123')
        
        # View leadership dashboard
        leadership_dashboard_response = self.client.get('/leadership/')
        self.assertEqual(leadership_dashboard_response.status_code, 200)
        self.assertContains(leadership_dashboard_response, 'Leadership Dashboard')
        
        # View pending requests
        pending_response = self.client.get('/pending/')
        self.assertEqual(pending_response.status_code, 200)
        self.assertContains(pending_response, 'Django Advanced Workshop')
        self.assertContains(pending_response, 'Team Member')
        
        # View request detail as leadership
        leadership_detail_response = self.client.get(f'/requests/{self.training_request.pk}/')
        self.assertEqual(leadership_detail_response.status_code, 200)
        self.assertTrue(leadership_detail_response.context['can_approve'])
        
        # Step 4: Leadership approves the request
        approve_response = self.client.post(
            f'/requests/{self.training_request.pk}/approve/',
            {'review_comments': 'Approved - this training aligns with our team development goals'},
            follow=True
        )
        self.assertEqual(approve_response.status_code, 200)
        
        # Verify request was approved
        self.training_request.refresh_from_db()
        self.assertEqual(self.training_request.status, 'APPROVED')
        self.assertEqual(self.training_request.reviewer, self.leadership)
        self.assertEqual(self.training_request.review_comments, 'Approved - this training aligns with our team development goals')
        self.assertIsNotNone(self.training_request.reviewed_at)
        
        # Step 5: Team member sees the approved status
        self.client.logout()
        self.client.login(username='teammember', password='testpass123')
        
        updated_detail_response = self.client.get(f'/requests/{self.training_request.pk}/')
        self.assertEqual(updated_detail_response.status_code, 200)
        self.assertContains(updated_detail_response, 'Approved')
        self.assertContains(updated_detail_response, 'this training aligns with our team development goals')
        
        # Step 6: Leadership marks training as completed
        self.client.logout()
        self.client.login(username='leadership', password='testpass123')
        
        complete_response = self.client.post(
            f'/requests/{self.training_request.pk}/complete/',
            {
                'completion_date': date.today().strftime('%Y-%m-%d'),
                'completion_notes': 'Training completed successfully. Great feedback from participant.'
            },
            follow=True
        )
        self.assertEqual(complete_response.status_code, 200)
        
        # Verify request was completed
        self.training_request.refresh_from_db()
        self.assertEqual(self.training_request.status, 'COMPLETED')
        self.assertIsNotNone(self.training_request.completed_at)
        self.assertEqual(self.training_request.completion_notes, 'Training completed successfully. Great feedback from participant.')
    
    def test_request_denial_workflow(self):
        """Test complete workflow for request denial"""
        # Create an expensive request for denial testing
        expensive_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Expensive Conference',
            description='Very expensive international conference',
            training_type='CONFERENCE',
            estimated_cost=Decimal('5000.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=60),
            end_date=date.today() + timedelta(days=65),
            justification='Would be nice to attend',
            status='PENDING'
        )
        
        # Step 1: Leadership denies the request
        self.client.login(username='leadership', password='testpass123')
        
        deny_response = self.client.post(
            f'/requests/{expensive_request.pk}/deny/',
            {'review_comments': 'Budget constraints this quarter. Please consider a more cost-effective alternative.'},
            follow=True
        )
        self.assertEqual(deny_response.status_code, 200)
        
        # Verify request was denied
        expensive_request.refresh_from_db()
        self.assertEqual(expensive_request.status, 'DENIED')
        self.assertEqual(expensive_request.reviewer, self.leadership)
        self.assertIn('Budget constraints', expensive_request.review_comments)
        
        # Step 2: Team member sees the denied status
        self.client.logout()
        self.client.login(username='teammember', password='testpass123')
        
        denied_detail_response = self.client.get(f'/requests/{expensive_request.pk}/')
        self.assertEqual(denied_detail_response.status_code, 200)
        self.assertContains(denied_detail_response, 'Denied')
        self.assertContains(denied_detail_response, 'Budget constraints')
    
    def test_multiple_requests_workflow(self):
        """Test workflow with multiple requests from same user"""
        # Create multiple requests for testing
        python_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Python Basics Course',
            description='Introduction to Python programming',
            training_type='COURSE',
            estimated_cost=Decimal('300.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=17),
            justification='Need to learn Python for automation tasks',
            status='PENDING'
        )
        
        react_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='React Development Workshop',
            description='Modern React development techniques',
            training_type='WORKSHOP',
            estimated_cost=Decimal('800.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=45),
            end_date=date.today() + timedelta(days=47),
            justification='Frontend development skills needed for upcoming project',
            status='PENDING'
        )
        
        # Step 1: Team member views all their requests
        self.client.login(username='teammember', password='testpass123')
        
        request_list_response = self.client.get('/requests/')
        self.assertEqual(request_list_response.status_code, 200)
        self.assertContains(request_list_response, 'Python Basics Course')
        self.assertContains(request_list_response, 'React Development Workshop')
        self.assertContains(request_list_response, 'Django Advanced Workshop')  # From setUp
        
        # Check dashboard shows correct statistics
        dashboard_response = self.client.get('/dashboard/')
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(dashboard_response.context['stats']['total_requests'], 3)
        self.assertEqual(dashboard_response.context['stats']['pending_requests'], 3)
        
        # Step 2: Leadership processes requests differently
        self.client.logout()
        self.client.login(username='leadership', password='testpass123')
        
        # Approve Python course
        self.client.post(
            f'/requests/{python_request.pk}/approve/',
            {'review_comments': 'Good foundational skill'},
            follow=True
        )
        
        # Deny React workshop
        self.client.post(
            f'/requests/{react_request.pk}/deny/',
            {'review_comments': 'Focus on backend skills first'},
            follow=True
        )
        
        # Verify final states
        python_request.refresh_from_db()
        react_request.refresh_from_db()
        self.assertEqual(python_request.status, 'APPROVED')
        self.assertEqual(react_request.status, 'DENIED')
        
        # Step 3: Team member sees mixed results
        self.client.logout()
        self.client.login(username='teammember', password='testpass123')
        
        final_dashboard_response = self.client.get('/dashboard/')
        self.assertEqual(final_dashboard_response.context['stats']['approved_requests'], 1)
        self.assertEqual(final_dashboard_response.context['stats']['denied_requests'], 1)
        self.assertEqual(final_dashboard_response.context['stats']['pending_requests'], 1)  # Original request still pending


class UserManagementWorkflowIntegrationTest(TestCase):
    """Integration tests for user management workflows through Django admin"""
    
    def setUp(self):
        """Set up test data for user management integration tests"""
        self.client = Client()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin.userprofile.role = 'ADMIN'
        self.admin.userprofile.save()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123',
            first_name='User',
            last_name='Two'
        )
    
    def test_complete_user_creation_and_role_assignment_workflow(self):
        """Test complete workflow for creating users and assigning roles through admin"""
        # Step 1: Admin logs into Django admin
        self.client.login(username='admin', password='adminpass123')
        
        # Access admin dashboard
        admin_response = self.client.get('/admin/')
        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, 'Django administration')
        
        # Step 2: Navigate to user management
        user_list_response = self.client.get('/admin/auth/user/')
        self.assertEqual(user_list_response.status_code, 200)
        self.assertContains(user_list_response, 'Users')
        
        # Verify existing users are displayed
        self.assertContains(user_list_response, 'user1')
        self.assertContains(user_list_response, 'user2')
        
        # Step 3: Create new user programmatically (simulating admin creation)
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='complexpass123',
            first_name='New',
            last_name='User'
        )
        
        # Verify user was created with default profile
        self.assertEqual(new_user.userprofile.role, 'TEAM_MEMBER')  # Default role
        
        # Step 4: View user in admin interface
        change_user_response = self.client.get(f'/admin/auth/user/{new_user.id}/change/')
        self.assertEqual(change_user_response.status_code, 200)
        self.assertContains(change_user_response, 'Change user')
        self.assertContains(change_user_response, 'newuser')
        
        # Step 5: Use bulk actions to manage multiple users
        bulk_action_data = {
            'action': 'make_leadership',
            '_selected_action': [str(self.user1.id), str(self.user2.id)],
        }
        
        bulk_response = self.client.post('/admin/auth/user/', bulk_action_data, follow=True)
        self.assertEqual(bulk_response.status_code, 200)
        
        # Verify bulk action worked
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertEqual(self.user1.userprofile.role, 'LEADERSHIP')
        self.assertEqual(self.user2.userprofile.role, 'LEADERSHIP')
    
    def test_user_deactivation_and_reactivation_workflow(self):
        """Test complete workflow for deactivating and reactivating users"""
        self.client.login(username='admin', password='adminpass123')
        
        # Step 1: Verify users are initially active
        self.assertTrue(self.user1.is_active)
        self.assertTrue(self.user1.userprofile.is_active)
        
        # Step 2: Deactivate users through bulk action
        deactivate_data = {
            'action': 'deactivate_users',
            '_selected_action': [str(self.user1.id), str(self.user2.id)],
        }
        
        deactivate_response = self.client.post('/admin/auth/user/', deactivate_data, follow=True)
        self.assertEqual(deactivate_response.status_code, 200)
        
        # Verify users were deactivated
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertFalse(self.user1.is_active)
        self.assertFalse(self.user1.userprofile.is_active)
        self.assertFalse(self.user2.is_active)
        self.assertFalse(self.user2.userprofile.is_active)
        
        # Step 3: Reactivate users through bulk action
        activate_data = {
            'action': 'activate_users',
            '_selected_action': [str(self.user1.id)],
        }
        
        activate_response = self.client.post('/admin/auth/user/', activate_data, follow=True)
        self.assertEqual(activate_response.status_code, 200)
        
        # Verify user was reactivated
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.is_active)
        self.assertTrue(self.user1.userprofile.is_active)
        
        # Verify user2 remains deactivated
        self.user2.refresh_from_db()
        self.assertFalse(self.user2.is_active)
    
    def test_userprofile_admin_workflow(self):
        """Test user management through UserProfile admin interface"""
        self.client.login(username='admin', password='adminpass123')
        
        # Step 1: Access UserProfile admin
        profile_list_response = self.client.get('/admin/accounts/userprofile/')
        self.assertEqual(profile_list_response.status_code, 200)
        self.assertContains(profile_list_response, 'User profiles')
        
        # Verify profiles are displayed
        self.assertContains(profile_list_response, 'user1')
        self.assertContains(profile_list_response, 'user2')
        
        # Step 2: Use bulk actions to change roles
        role_change_data = {
            'action': 'set_leadership_role',
            '_selected_action': [str(self.user1.userprofile.id)],
        }
        
        role_response = self.client.post('/admin/accounts/userprofile/', role_change_data)
        self.assertEqual(role_response.status_code, 302)
        
        # Verify role was changed
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.userprofile.role, 'LEADERSHIP')
        
        # Step 3: Filter and search functionality
        # Test role filter
        filter_response = self.client.get('/admin/accounts/userprofile/?role=LEADERSHIP')
        self.assertEqual(filter_response.status_code, 200)
        self.assertContains(filter_response, 'user1')
        
        # Test search
        search_response = self.client.get('/admin/accounts/userprofile/?q=user1')
        self.assertEqual(search_response.status_code, 200)
        self.assertContains(search_response, 'user1')


class CrossModuleIntegrationTest(TestCase):
    """Integration tests that span multiple modules and test system-wide workflows"""
    
    def setUp(self):
        """Set up test data for cross-module integration tests"""
        self.client = Client()
        
        # Create complete user hierarchy
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin.userprofile.role = 'ADMIN'
        self.admin.userprofile.save()
        
        self.leadership = User.objects.create_user(
            username='leadership',
            email='leadership@example.com',
            password='testpass123'
        )
        self.leadership.userprofile.role = 'LEADERSHIP'
        self.leadership.userprofile.save()
        
        self.team_member = User.objects.create_user(
            username='teammember',
            email='teammember@example.com',
            password='testpass123'
        )
        self.team_member.userprofile.role = 'TEAM_MEMBER'
        self.team_member.userprofile.save()
    
    def test_new_user_complete_system_workflow(self):
        """Test complete workflow from user creation to training request completion"""
        # Step 1: Admin creates new user
        self.client.login(username='admin', password='adminpass123')
        
        # Create user through admin interface
        new_user_data = {
            'username': 'newemployee',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        }
        
        self.client.post('/admin/auth/user/add/', new_user_data)
        new_user = User.objects.get(username='newemployee')
        
        # Step 2: New user logs in and submits training request
        self.client.logout()
        self.client.login(username='newemployee', password='complexpass123')
        
        # Access dashboard
        dashboard_response = self.client.get(reverse('training_requests:dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        
        # Submit training request
        request_data = {
            'title': 'Onboarding Training',
            'description': 'Essential skills training for new employee',
            'training_type': 'COURSE',
            'estimated_cost': '500.00',
            'currency': 'USD',
            'start_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=9)).strftime('%Y-%m-%d'),
            'justification': 'Required for role competency'
        }
        
        self.client.post(reverse('training_requests:create_request'), request_data)
        training_request = TrainingRequest.objects.get(title='Onboarding Training')
        
        # Step 3: Leadership approves request
        self.client.logout()
        self.client.login(username='leadership', password='testpass123')
        
        self.client.post(
            reverse('training_requests:approve_request', kwargs={'pk': training_request.pk}),
            {'review_comments': 'Essential for new employee success'}
        )
        
        # Step 4: Admin promotes user to leadership after training
        self.client.logout()
        self.client.login(username='admin', password='adminpass123')
        
        # Change user role through bulk action
        promote_data = {
            'action': 'make_leadership',
            '_selected_action': [str(new_user.id)],
        }
        
        self.client.post('/admin/auth/user/', promote_data)
        
        # Step 5: Verify new leadership user can now approve requests
        self.client.logout()
        self.client.login(username='newemployee', password='complexpass123')
        
        # Create another request from team member
        self.client.logout()
        self.client.login(username='teammember', password='testpass123')
        
        another_request_data = {
            'title': 'Advanced Skills Training',
            'description': 'Advanced technical skills development',
            'training_type': 'WORKSHOP',
            'estimated_cost': '800.00',
            'currency': 'USD',
            'start_date': (date.today() + timedelta(days=20)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=22)).strftime('%Y-%m-%d'),
            'justification': 'Career development'
        }
        
        self.client.post(reverse('training_requests:create_request'), another_request_data)
        another_request = TrainingRequest.objects.get(title='Advanced Skills Training')
        
        # Step 6: Newly promoted leadership user approves the request
        self.client.logout()
        self.client.login(username='newemployee', password='complexpass123')
        
        # Verify user can access leadership features
        leadership_dashboard_response = self.client.get(reverse('training_requests:leadership_dashboard'))
        self.assertEqual(leadership_dashboard_response.status_code, 200)
        
        # Approve the request
        approve_response = self.client.post(
            reverse('training_requests:approve_request', kwargs={'pk': another_request.pk}),
            {'review_comments': 'Approved by newly promoted leadership'}
        )
        self.assertEqual(approve_response.status_code, 302)
        
        # Verify approval worked
        another_request.refresh_from_db()
        self.assertEqual(another_request.status, 'APPROVED')
        self.assertEqual(another_request.reviewer.username, 'newemployee')
    
    def test_role_change_permission_workflow(self):
        """Test that role changes immediately affect user permissions"""
        # Step 1: Team member cannot access leadership features
        self.client.login(username='teammember', password='testpass123')
        
        leadership_response = self.client.get(reverse('training_requests:leadership_dashboard'))
        self.assertEqual(leadership_response.status_code, 403)  # Forbidden
        
        # Step 2: Admin promotes team member to leadership
        self.client.logout()
        self.client.login(username='admin', password='adminpass123')
        
        promote_data = {
            'action': 'make_leadership',
            '_selected_action': [str(self.team_member.id)],
        }
        
        self.client.post('/admin/auth/user/', promote_data)
        
        # Step 3: User can now access leadership features
        self.client.logout()
        self.client.login(username='teammember', password='testpass123')
        
        # Should now have access to leadership dashboard
        new_leadership_response = self.client.get(reverse('training_requests:leadership_dashboard'))
        self.assertEqual(new_leadership_response.status_code, 200)
        
        # Should be able to view pending requests
        pending_response = self.client.get(reverse('training_requests:pending_requests'))
        self.assertEqual(pending_response.status_code, 200)
        
        # Step 4: Admin demotes user back to team member
        self.client.logout()
        self.client.login(username='admin', password='adminpass123')
        
        demote_data = {
            'action': 'make_team_members',
            '_selected_action': [str(self.team_member.id)],
        }
        
        self.client.post('/admin/auth/user/', demote_data)
        
        # Step 5: User loses leadership access
        self.client.logout()
        self.client.login(username='teammember', password='testpass123')
        
        # Should no longer have access to leadership features
        revoked_leadership_response = self.client.get(reverse('training_requests:leadership_dashboard'))
        self.assertEqual(revoked_leadership_response.status_code, 403)
    
    def test_user_deactivation_system_wide_effects(self):
        """Test that user deactivation affects all system interactions"""
        # Step 1: Create training request as team member
        self.client.login(username='teammember', password='testpass123')
        
        request_data = {
            'title': 'Test Training',
            'description': 'Test training request',
            'training_type': 'COURSE',
            'estimated_cost': '300.00',
            'currency': 'USD',
            'start_date': (date.today() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=12)).strftime('%Y-%m-%d'),
            'justification': 'Testing purposes'
        }
        
        self.client.post(reverse('training_requests:create_request'), request_data)
        training_request = TrainingRequest.objects.get(title='Test Training')
        
        # Step 2: Admin deactivates user
        self.client.logout()
        self.client.login(username='admin', password='adminpass123')
        
        deactivate_data = {
            'action': 'deactivate_users',
            '_selected_action': [str(self.team_member.id)],
        }
        
        self.client.post('/admin/auth/user/', deactivate_data)
        
        # Step 3: Deactivated user cannot log in
        self.client.logout()
        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'teammember',
            'password': 'testpass123'
        })
        
        # Should stay on login page (user is inactive)
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, 'Please enter a correct username and password')
        
        # Step 4: Training request still exists but user is marked inactive
        self.team_member.refresh_from_db()
        self.assertFalse(self.team_member.is_active)
        self.assertFalse(self.team_member.userprofile.is_active)
        
        # Request still exists in system
        self.assertTrue(TrainingRequest.objects.filter(title='Test Training').exists())
        
        # Step 5: Admin reactivates user
        self.client.login(username='admin', password='adminpass123')
        
        activate_data = {
            'action': 'activate_users',
            '_selected_action': [str(self.team_member.id)],
        }
        
        self.client.post('/admin/auth/user/', activate_data)
        
        # Step 6: User can log in again and access their requests
        self.client.logout()
        login_response = self.client.post(reverse('accounts:login'), {
            'username': 'teammember',
            'password': 'testpass123'
        })
        
        self.assertEqual(login_response.status_code, 302)  # Successful login redirect
        
        # User can see their training request
        request_list_response = self.client.get(reverse('training_requests:request_list'))
        self.assertEqual(request_list_response.status_code, 200)
        self.assertContains(request_list_response, 'Test Training')