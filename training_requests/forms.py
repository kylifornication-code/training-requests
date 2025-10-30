from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from .models import TrainingRequest


class TrainingRequestForm(forms.ModelForm):
    """Form for creating and editing training requests"""
    
    class Meta:
        model = TrainingRequest
        fields = [
            'title', 'description', 'training_type', 'estimated_cost', 
            'currency', 'start_date', 'end_date', 'justification', 'supporting_documents'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter training title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the training content and objectives'
            }),
            'training_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '3',
                'placeholder': 'USD'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'justification': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explain how this training will benefit your role and the team'
            }),
            'supporting_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt'
            }),
        }
    
    def clean_start_date(self):
        """Validate that start date is not in the past"""
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < date.today():
            raise ValidationError("Start date cannot be in the past.")
        return start_date
    
    def clean_end_date(self):
        """Validate that end date is not before start date"""
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError("End date cannot be before start date.")
        
        return end_date
    
    def clean_estimated_cost(self):
        """Validate that estimated cost is positive"""
        cost = self.cleaned_data.get('estimated_cost')
        if cost is not None and cost < 0:
            raise ValidationError("Estimated cost must be a positive number.")
        return cost
    
    def clean_currency(self):
        """Validate and normalize currency code"""
        currency = self.cleaned_data.get('currency')
        if currency:
            currency = currency.upper().strip()
            if len(currency) != 3:
                raise ValidationError("Currency code must be exactly 3 characters (e.g., USD, EUR).")
            # Check for common currency codes
            valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'CNY', 'INR']
            if currency not in valid_currencies:
                # Still allow other currencies but show a warning in the help text
                pass
        return currency
    
    def clean_supporting_documents(self):
        """Additional validation for supporting documents"""
        file = self.cleaned_data.get('supporting_documents')
        if file:
            # Additional file name validation
            if len(file.name) > 255:
                raise ValidationError("File name is too long. Please use a shorter file name.")
            
            # Check for potentially dangerous file names
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
            if any(char in file.name for char in dangerous_chars):
                raise ValidationError("File name contains invalid characters.")
        
        return file


class RequestReviewForm(forms.Form):
    """Form for reviewing training requests (approve/deny)"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('deny', 'Deny'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    review_comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add comments about your decision...'
        }),
        help_text="Comments are optional for approval, but required for denial."
    )
    
    def clean(self):
        """Validate that denial requires comments"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        review_comments = cleaned_data.get('review_comments', '').strip()
        
        if action == 'deny' and not review_comments:
            raise ValidationError("Comments are required when denying a request.")
        
        return cleaned_data


class RequestCompletionForm(forms.Form):
    """Form for marking training requests as completed"""
    
    completion_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="Date when the training was completed (defaults to today if not specified)."
    )
    
    completion_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add notes about the training completion...'
        }),
        help_text="Optional notes about the training completion."
    )
    
    def clean_completion_date(self):
        """Validate that completion date is not in the future"""
        completion_date = self.cleaned_data.get('completion_date')
        if completion_date and completion_date > date.today():
            raise ValidationError("Completion date cannot be in the future.")
        return completion_date


class RequestFilterForm(forms.Form):
    """Form for filtering training requests"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, description, or requester'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + TrainingRequest.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    training_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + TrainingRequest.TRAINING_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        """Validate date range"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Start date cannot be after end date.")
        
        return cleaned_data


class BulkActionForm(forms.Form):
    """Form for handling bulk actions on training requests"""
    
    ACTION_CHOICES = [
        ('approve', 'Approve All Selected'),
        ('deny', 'Deny All Selected'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    review_comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add comments for all selected requests...'
        }),
        help_text="Comments are optional for approvals but required for denials."
    )
    
    selected_requests = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    def clean(self):
        """Validate that denial requires comments"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        review_comments = cleaned_data.get('review_comments', '').strip()
        
        if action == 'deny' and not review_comments:
            raise ValidationError("Comments are required when denying requests.")
        
        return cleaned_data


class CommentForm(forms.Form):
    """Simple form for adding comments to training requests"""
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add your comment...'
        }),
        help_text="Share your thoughts or ask questions about this request."
    )


class CompletedTrainingFilterForm(forms.Form):
    """Form for filtering completed training reports"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, description, or team member'
        })
    )
    
    team_member = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by team member name'
        })
    )
    
    training_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + TrainingRequest.TRAINING_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    completion_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Completed From"
    )
    
    completion_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Completed To"
    )
    
    def clean(self):
        """Validate date range"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('completion_date_from')
        date_to = cleaned_data.get('completion_date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Start date cannot be after end date.")
        
        return cleaned_data