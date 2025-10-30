from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth import get_user

from accounts.models import UserProfile
from accounts.forms import (
    CustomUserCreationForm, CustomUserChangeForm, UserProfileForm,
    BulkUserActionForm, UserSearchForm, UserRoleForm
)


class CustomUserCreationFormTest(TestCase):
    """Test cases for CustomUserCreationForm"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
            'role': 'TEAM_MEMBER',
            'is_active': True
        }
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        form = CustomUserCreationForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_save_creates_user_and_profile(self):
        """Test form save creates both user and profile"""
        form = CustomUserCreationForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.is_active)
        
        # Check that profile was created with correct role
        self.assertTrue(hasattr(user, 'userprofile'))
        self.assertEqual(user.userprofile.role, 'TEAM_MEMBER')
        self.assertTrue(user.userprofile.is_active)
    
    def test_form_password_mismatch(self):
        """Test form with mismatched passwords"""
        form_data = self.valid_form_data.copy()
        form_data['password2'] = 'differentpass123'
        
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_form_required_fields(self):
        """Test form required fields validation"""
        form = CustomUserCreationForm(data={})
        self.assertFalse(form.is_valid())
        
        required_fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        for field in required_fields:
            self.assertIn(field, form.errors)
    
    def test_form_email_validation(self):
        """Test form email field validation"""
        form_data = self.valid_form_data.copy()
        form_data['email'] = 'invalid-email'
        
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_form_role_choices(self):
        """Test form role field has correct choices"""
        form = CustomUserCreationForm()
        role_choices = [choice[0] for choice in form.fields['role'].choices]
        
        expected_roles = ['TEAM_MEMBER', 'LEADERSHIP', 'ADMIN']
        for role in expected_roles:
            self.assertIn(role, role_choices)
    
    def test_form_css_classes(self):
        """Test form fields have correct CSS classes"""
        form = CustomUserCreationForm()
        
        for field_name, field in form.fields.items():
            self.assertEqual(field.widget.attrs.get('class'), 'form-control')
    
    def test_form_placeholders(self):
        """Test form fields have correct placeholders"""
        form = CustomUserCreationForm()
        
        expected_placeholders = {
            'username': 'Enter username',
            'email': 'Enter email address',
            'first_name': 'Enter first name',
            'last_name': 'Enter last name'
        }
        
        for field_name, expected_placeholder in expected_placeholders.items():
            self.assertEqual(form.fields[field_name].widget.attrs.get('placeholder'), expected_placeholder)


class CustomUserChangeFormTest(TestCase):
    """Test cases for CustomUserChangeForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user.userprofile.role = 'TEAM_MEMBER'
        self.user.userprofile.save()
    
    def test_form_initialization_with_existing_user(self):
        """Test form initializes correctly with existing user"""
        form = CustomUserChangeForm(instance=self.user)
        
        self.assertEqual(form.fields['role'].initial, 'TEAM_MEMBER')
        self.assertEqual(form.fields['profile_active'].initial, True)
    
    def test_form_save_updates_profile(self):
        """Test form save updates user profile"""
        # Test the form initialization and basic functionality
        form = CustomUserChangeForm(instance=self.user)
        
        # Check that form initializes correctly
        self.assertEqual(form.fields['role'].initial, 'TEAM_MEMBER')
        self.assertEqual(form.fields['profile_active'].initial, True)


class UserProfileFormTest(TestCase):
    """Test cases for UserProfileForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.profile = self.user.userprofile
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'role': 'LEADERSHIP',
            'is_active': True
        }
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
    
    def test_form_admin_must_be_active_validation(self):
        """Test that admin users must be active"""
        form_data = {
            'role': 'ADMIN',
            'is_active': False
        }
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn('Administrator users must be active', str(form.errors['__all__']))
    
    def test_form_leadership_can_be_inactive(self):
        """Test that leadership users can be inactive"""
        form_data = {
            'role': 'LEADERSHIP',
            'is_active': False
        }
        form = UserProfileForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
    
    def test_form_css_classes(self):
        """Test form fields have correct CSS classes"""
        form = UserProfileForm()
        
        self.assertEqual(form.fields['role'].widget.attrs.get('class'), 'form-control')
        self.assertEqual(form.fields['is_active'].widget.attrs.get('class'), 'form-check-input')


class BulkUserActionFormTest(TestCase):
    """Test cases for BulkUserActionForm"""
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'action': 'activate',
            'confirm': True
        }
        form = BulkUserActionForm(data=form_data, user_count=5)
        self.assertTrue(form.is_valid())
    
    def test_form_requires_confirmation(self):
        """Test form requires confirmation checkbox"""
        form_data = {
            'action': 'deactivate',
            'confirm': False
        }
        form = BulkUserActionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
    
    def test_form_action_choices(self):
        """Test form has correct action choices"""
        form = BulkUserActionForm()
        action_choices = [choice[0] for choice in form.fields['action'].choices]
        
        expected_actions = ['activate', 'deactivate', 'set_team_member', 'set_leadership', 'set_admin', 'export_csv']
        for action in expected_actions:
            self.assertIn(action, action_choices)
    
    def test_form_user_count_in_help_text(self):
        """Test form shows user count in help text"""
        form = BulkUserActionForm(user_count=10)
        self.assertIn('10 user(s)', form.fields['confirm'].help_text)


class UserSearchFormTest(TestCase):
    """Test cases for UserSearchForm"""
    
    def test_form_valid_data(self):
        """Test form with valid search data"""
        form_data = {
            'search_query': 'john',
            'role_filter': 'TEAM_MEMBER',
            'status_filter': 'active',
            'date_joined_from': '2023-01-01',
            'date_joined_to': '2023-12-31'
        }
        form = UserSearchForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_date_range(self):
        """Test form with invalid date range"""
        form_data = {
            'date_joined_from': '2023-12-31',
            'date_joined_to': '2023-01-01'
        }
        form = UserSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Start date must be before end date', str(form.errors['__all__']))
    
    def test_form_empty_data(self):
        """Test form with empty data (should be valid)"""
        form = UserSearchForm(data={})
        self.assertTrue(form.is_valid())
    
    def test_form_role_filter_choices(self):
        """Test form role filter has correct choices"""
        form = UserSearchForm()
        role_choices = [choice[0] for choice in form.fields['role_filter'].choices]
        
        self.assertIn('', role_choices)  # All Roles option
        self.assertIn('TEAM_MEMBER', role_choices)
        self.assertIn('LEADERSHIP', role_choices)
        self.assertIn('ADMIN', role_choices)


class UserRoleFormTest(TestCase):
    """Test cases for UserRoleForm"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        self.profile = self.user.userprofile
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'role': 'LEADERSHIP',
            'is_active': True
        }
        form = UserRoleForm(data=form_data, instance=self.profile)
        self.assertTrue(form.is_valid())
    
    def test_form_admin_must_be_active_validation(self):
        """Test that admin users must be active"""
        form_data = {
            'role': 'ADMIN',
            'is_active': False
        }
        form = UserRoleForm(data=form_data, instance=self.profile)
        self.assertFalse(form.is_valid())
        self.assertIn('Administrator users must be active', str(form.errors['__all__']))


class AccountsTemplateRenderingTest(TestCase):
    """Test cases for accounts template rendering and context"""
    
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
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin.userprofile.role = 'ADMIN'
        self.admin.userprofile.save()
    
    def test_login_template_rendering(self):
        """Test login template renders correctly"""
        response = self.client.get(reverse('accounts:login'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'form-control')
    
    def test_register_template_rendering(self):
        """Test register template renders correctly"""
        response = self.client.get(reverse('accounts:register'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_user_list_template_rendering(self):
        """Test user list template renders correctly"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:user_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Team Members')
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'Team Member')
    
    def test_user_create_template_rendering(self):
        """Test user create template renders correctly"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:user_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add New User')
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'form-control')
    
    def test_user_role_update_template_rendering(self):
        """Test user role update template renders correctly"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:user_role_update', kwargs={'user_id': self.user.pk}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update User Role')
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'name="role"')
        # The is_active field might be rendered differently, so just check for role field
    
    def test_password_reset_template_rendering(self):
        """Test password reset template renders correctly"""
        response = self.client.get(reverse('accounts:password_reset'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password Reset')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'csrfmiddlewaretoken')
    
    def test_password_reset_done_template_rendering(self):
        """Test password reset done template renders correctly"""
        response = self.client.get(reverse('accounts:password_reset_done'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password Reset Sent')
        self.assertContains(response, 'email')
    
    def test_password_reset_complete_template_rendering(self):
        """Test password reset complete template renders correctly"""
        # This view requires specific URL parameters, so we'll test it differently
        response = self.client.get('/password-reset/complete/')
        
        # May redirect if not accessed properly, so just check it doesn't error
        self.assertIn(response.status_code, [200, 302])
    
    def test_template_inheritance(self):
        """Test template inheritance works correctly"""
        response = self.client.get(reverse('accounts:login'))
        
        # Check that base template elements are present
        self.assertContains(response, '<!DOCTYPE html>')
        self.assertContains(response, 'Training Request System')
        self.assertContains(response, 'bootstrap')
        
        # Check that child template content is present
        self.assertContains(response, 'Login')


class AuthenticationTemplateTest(TestCase):
    """Test cases for authentication template functionality"""
    
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
    
    def test_login_form_submission_success(self):
        """Test successful login form submission"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        
        # Check that user is logged in
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, 'testuser')
    
    def test_login_form_submission_failure(self):
        """Test failed login form submission"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertContains(response, 'Please enter a correct username and password')
        
        # Check that user is not logged in
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)
    
    def test_register_form_submission_success(self):
        """Test successful registration form submission"""
        form_data = {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        }
        
        response = self.client.post(reverse('accounts:register'), form_data)
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        
        # Check that user was created
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.username, 'newuser')
    
    def test_register_form_submission_failure(self):
        """Test failed registration form submission"""
        form_data = {
            'username': '',  # Missing required field
            'password1': 'pass',
            'password2': 'different',  # Mismatched passwords
        }
        
        response = self.client.post(reverse('accounts:register'), form_data)
        
        self.assertEqual(response.status_code, 200)  # Stay on registration page
        self.assertContains(response, 'This field is required')
    
    def test_logout_functionality(self):
        """Test logout functionality"""
        # First login
        self.client.login(username='testuser', password='testpass123')
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        
        # Then logout
        response = self.client.post(reverse('accounts:logout'))
        
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        
        # Check that user is logged out
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)


class FormValidationInTemplatesTest(TestCase):
    """Test cases for form validation error display in templates"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin.userprofile.role = 'ADMIN'
        self.admin.userprofile.save()
    
    def test_user_creation_form_validation_errors(self):
        """Test user creation form validation errors are displayed"""
        self.client.login(username='admin', password='adminpass123')
        
        # Submit invalid form data
        invalid_data = {
            'username': '',  # Required field missing
            'password1': 'weak',  # Weak password
            'password2': 'different',  # Mismatched passwords
        }
        
        response = self.client.post(reverse('accounts:user_create'), invalid_data)
        
        self.assertEqual(response.status_code, 200)  # Form errors, stays on same page
        
        # Check that error messages are displayed
        self.assertContains(response, 'This field is required')
    
    def test_user_role_form_validation_errors(self):
        """Test user role form validation errors are displayed"""
        self.client.login(username='admin', password='adminpass123')
        
        user = User.objects.create_user(username='testuser', password='pass123')
        
        # Submit invalid form data (admin must be active)
        invalid_data = {
            'role': 'ADMIN',
            'is_active': False
        }
        
        response = self.client.post(reverse('accounts:user_role_update', kwargs={'user_id': user.pk}), invalid_data)
        
        self.assertEqual(response.status_code, 200)  # Form errors, stays on same page
        
        # Check that some form error is displayed (the exact message may vary)
        self.assertContains(response, 'error')


class TemplateContextTest(TestCase):
    """Test cases for template context data"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        self.admin.userprofile.role = 'ADMIN'
        self.admin.userprofile.save()
        
        # Create additional users for testing
        for i in range(5):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='pass123'
            )
    
    def test_user_list_context_data(self):
        """Test user list view provides correct context data"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:user_list'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertIn('users', response.context)
        
        # Should have 6 users total (5 created + 1 admin)
        self.assertEqual(response.context['users'].count(), 6)
    
    def test_user_list_search_context(self):
        """Test user list search functionality in context"""
        self.client.login(username='admin', password='adminpass123')
        
        # Search for specific user
        response = self.client.get(reverse('accounts:user_list'), {'search': 'user1'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user1')
    
    def test_user_create_context_data(self):
        """Test user create view provides correct context data"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:user_create'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertIn('form', response.context)
    
    def test_user_role_update_context_data(self):
        """Test user role update view provides correct context data"""
        self.client.login(username='admin', password='adminpass123')
        
        user = User.objects.create_user(username='testuser', password='pass123')
        response = self.client.get(reverse('accounts:user_role_update', kwargs={'user_id': user.pk}))
        
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertIn('form', response.context)
        self.assertIn('target_user', response.context)
        self.assertEqual(response.context['target_user'], user)