from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from training_requests.models import TrainingRequest
from datetime import date, timedelta
from decimal import Decimal


class ReportsViewsTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create a leadership user
        self.leadership_user = User.objects.create_user(
            username='leader',
            email='leader@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Leader'
        )
        profile, created = UserProfile.objects.get_or_create(
            user=self.leadership_user,
            defaults={'role': 'LEADERSHIP'}
        )
        if not created:
            profile.role = 'LEADERSHIP'
            profile.save()
        
        # Create a team member
        self.team_member = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Member'
        )
        profile, created = UserProfile.objects.get_or_create(
            user=self.team_member,
            defaults={'role': 'TEAM_MEMBER'}
        )
        if not created:
            profile.role = 'TEAM_MEMBER'
            profile.save()
        
        # Create some test training requests
        self.completed_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Test Training',
            description='Test description',
            training_type='COURSE',
            estimated_cost=Decimal('1000.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            justification='Test justification',
            status='COMPLETED'
        )
        
        self.pending_request = TrainingRequest.objects.create(
            requester=self.team_member,
            title='Pending Training',
            description='Pending description',
            training_type='CONFERENCE',
            estimated_cost=Decimal('2000.00'),
            currency='USD',
            start_date=date.today() + timedelta(days=60),
            end_date=date.today() + timedelta(days=62),
            justification='Pending justification',
            status='PENDING'
        )
    
    def test_analytics_dashboard_access_leadership(self):
        """Test that leadership can access analytics dashboard"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('reports:analytics_dashboard'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')
    
    def test_analytics_dashboard_access_team_member(self):
        """Test that team members cannot access analytics dashboard"""
        self.client.login(username='member', password='testpass123')
        response = self.client.get(reverse('reports:analytics_dashboard'))
        # Should redirect to login or show permission denied
        self.assertIn(response.status_code, [302, 403])
    
    def test_budget_analysis_api(self):
        """Test budget analysis API endpoint"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('reports:budget_analysis_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Check that response contains expected data structure
        data = response.json()
        self.assertIn('monthly_budget', data)
        self.assertIn('type_budget', data)
        self.assertIn('status_distribution', data)
    
    def test_team_performance_api(self):
        """Test team performance API endpoint"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('reports:team_performance_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Check that response contains expected data structure
        data = response.json()
        self.assertIn('most_active', data)
        self.assertIn('highest_investment', data)
    
    def test_export_analytics_pdf(self):
        """Test PDF export functionality"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('reports:export_analytics_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="training_analytics_'))
    
    def test_export_budget_csv(self):
        """Test CSV export functionality"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('reports:export_budget_analysis_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="budget_analysis_'))
    
    def test_analytics_dashboard_context_data(self):
        """Test that analytics dashboard provides correct context data"""
        self.client.login(username='leader', password='testpass123')
        response = self.client.get(reverse('reports:analytics_dashboard'))
        
        # Check that key statistics are present
        self.assertIn('total_requests', response.context)
        self.assertIn('pending_requests', response.context)
        self.assertIn('completed_requests', response.context)
        self.assertIn('total_budget_allocated', response.context)
        self.assertIn('training_type_stats', response.context)
        self.assertIn('monthly_trends', response.context)
        self.assertIn('team_performance', response.context)
        
        # Verify the statistics match our test data
        self.assertEqual(response.context['total_requests'], 2)
        self.assertEqual(response.context['pending_requests'], 1)
        self.assertEqual(response.context['completed_requests'], 1)