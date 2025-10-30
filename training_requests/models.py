from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import os


def validate_file_size(value):
    """Validate that uploaded file is not larger than 10MB"""
    filesize = value.size
    if filesize > 10 * 1024 * 1024:  # 10MB in bytes
        raise ValidationError("File size cannot exceed 10MB.")
    return value


class TrainingRequest(models.Model):
    TRAINING_TYPE_CHOICES = [
        ('CONFERENCE', 'Conference'),
        ('COURSE', 'Course'),
        ('CERTIFICATION', 'Certification'),
        ('WORKSHOP', 'Workshop'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
        ('COMPLETED', 'Completed'),
    ]
    
    requester = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='training_requests',
        help_text="User who submitted the training request"
    )
    title = models.CharField(max_length=200, help_text="Training title or name")
    description = models.TextField(help_text="Detailed description of the training")
    training_type = models.CharField(
        max_length=20, 
        choices=TRAINING_TYPE_CHOICES,
        help_text="Type of training being requested"
    )
    estimated_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Estimated cost in the specified currency"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code (e.g., USD, EUR)")
    start_date = models.DateField(help_text="Training start date")
    end_date = models.DateField(help_text="Training end date")
    justification = models.TextField(help_text="Business justification for the training")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        help_text="Current status of the request"
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_requests',
        help_text="Leadership member who reviewed the request"
    )
    review_comments = models.TextField(
        blank=True, 
        help_text="Comments from the reviewer"
    )
    reviewed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the request was reviewed"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the training was completed"
    )
    completion_notes = models.TextField(
        blank=True,
        help_text="Notes about the training completion"
    )
    supporting_documents = models.FileField(
        upload_to='training_requests/documents/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'txt'],
                message="Only PDF, DOC, DOCX, and TXT files are allowed."
            ),
            validate_file_size
        ],
        help_text="Optional supporting documents (PDF, DOC, DOCX, TXT, up to 10MB)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.requester.username} ({self.get_status_display()})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Start date cannot be after end date")
    
    class Meta:
        verbose_name = "Training Request"
        verbose_name_plural = "Training Requests"
        ordering = ['-created_at']
