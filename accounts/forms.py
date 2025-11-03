from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Enhanced user creation form for admin interface"""
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    first_name = forms.CharField(max_length=30, required=True, help_text="Required.")
    last_name = forms.CharField(max_length=30, required=True, help_text="Required.")
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        initial='TEAM_MEMBER',
        help_text="Select the user's role in the system."
    )
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Designates whether this user should be treated as active."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role', 'is_active')

    def __init__(self, *args, **kwargs):
        # Extract current_user if provided
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes for better styling
        for field_name, field in self.fields.items():
            widget = field.widget
            if hasattr(widget, 'input_type'):
                if widget.input_type in ['checkbox', 'radio']:
                    widget.attrs['class'] = 'form-check-input'
                elif widget.input_type == 'select':
                    widget.attrs['class'] = 'form-select'
                else:
                    widget.attrs['class'] = 'form-control'
            elif widget.__class__.__name__ in ['Select', 'SelectMultiple']:
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'
        
        # Add placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Enter username'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter email address'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        
        # Restrict role choices based on current user's role if provided
        if self.current_user and hasattr(self.current_user, 'userprofile'):
            current_role = self.current_user.userprofile.role
            if current_role == 'LEADERSHIP':
                # Leadership can only create team members
                self.fields['role'].choices = [
                    ('TEAM_MEMBER', 'Team Member')
                ]
            elif current_role == 'ADMIN':
                # Admin can create any role
                pass  # Keep all choices
            else:
                # Team members shouldn't be able to create users, but just in case
                self.fields['role'].choices = [
                    ('TEAM_MEMBER', 'Team Member')
                ]

        # Hide is_active for public registration (no logged-in creator)
        # or when the creator is not an admin. Public sign-ups should always
        # be created as active users.
        if not (self.current_user and hasattr(self.current_user, 'userprofile') and self.current_user.userprofile.role == 'ADMIN'):
            # Remove the field from the form so it doesn't affect cleaned_data
            if 'is_active' in self.fields:
                self.fields.pop('is_active')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # Ensure public registrations are always active. When the field is
        # not present (public or non-admin), default to True.
        if 'is_active' in self.cleaned_data:
            user.is_active = self.cleaned_data['is_active']
        else:
            user.is_active = True
        
        if commit:
            user.save()
            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            # Keep profile active in sync with user active
            if 'is_active' in self.cleaned_data:
                profile.is_active = self.cleaned_data['is_active']
            else:
                profile.is_active = True
            profile.save()
        
        return user


class CustomUserChangeForm(UserChangeForm):
    """Enhanced user change form for admin interface"""
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=False,
        help_text="Select the user's role in the system."
    )
    profile_active = forms.BooleanField(
        required=False,
        help_text="Designates whether this user's profile should be treated as active."
    )

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize role and profile_active fields if user has a profile
        if self.instance and hasattr(self.instance, 'userprofile'):
            self.fields['role'].initial = self.instance.userprofile.role
            self.fields['profile_active'].initial = self.instance.userprofile.is_active
        
        # Add CSS classes for better styling
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit)
        
        if commit and 'role' in self.cleaned_data:
            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            if 'role' in self.cleaned_data and self.cleaned_data['role']:
                profile.role = self.cleaned_data['role']
            if 'profile_active' in self.cleaned_data:
                profile.is_active = self.cleaned_data['profile_active']
            profile.save()
        
        return user


class UserProfileForm(forms.ModelForm):
    """Form for UserProfile model with enhanced validation"""
    
    class Meta:
        model = UserProfile
        fields = ['role', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['role'].help_text = "Select the user's role in the training request system."
        self.fields['is_active'].help_text = "Uncheck to deactivate this user's profile without deleting the account."

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        is_active = cleaned_data.get('is_active')
        
        # Validation: Admin users should be active
        if role == 'ADMIN' and not is_active:
            raise forms.ValidationError("Administrator users must be active.")
        
        return cleaned_data


class BulkUserActionForm(forms.Form):
    """Form for bulk user actions in admin interface"""
    ACTION_CHOICES = [
        ('activate', 'Activate Users'),
        ('deactivate', 'Deactivate Users'),
        ('set_team_member', 'Set as Team Members'),
        ('set_leadership', 'Set as Leadership'),
        ('set_admin', 'Set as Administrators'),
        ('export_csv', 'Export to CSV'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    confirm = forms.BooleanField(
        required=True,
        help_text="Check this box to confirm the bulk action."
    )

    def __init__(self, *args, **kwargs):
        self.user_count = kwargs.pop('user_count', 0)
        super().__init__(*args, **kwargs)
        
        if self.user_count:
            self.fields['confirm'].help_text = f"Check this box to confirm applying this action to {self.user_count} user(s)."


class UserSearchForm(forms.Form):
    """Enhanced search form for user management"""
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username, email, or name...'
        })
    )
    role_filter = forms.ChoiceField(
        choices=[('', 'All Roles')] + UserProfile.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status_filter = forms.ChoiceField(
        choices=[
            ('', 'All Users'),
            ('active', 'Active Users'),
            ('inactive', 'Inactive Users'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_joined_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_joined_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_joined_from')
        date_to = cleaned_data.get('date_joined_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Start date must be before end date.")
        
        return cleaned_data


class UserRoleForm(forms.ModelForm):
    """Form for updating user roles"""
    
    class Meta:
        model = UserProfile
        fields = ['role', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['role'].help_text = "Select the user's role in the training request system."
        self.fields['is_active'].help_text = "Uncheck to deactivate this user without deleting the account."

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        is_active = cleaned_data.get('is_active')
        
        # Validation: Admin users should be active
        if role == 'ADMIN' and not is_active:
            raise forms.ValidationError("Administrator users must be active.")
        
        return cleaned_data