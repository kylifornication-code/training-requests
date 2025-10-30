"""
Utility functions for the training system application.
"""
import os
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_file_upload(uploaded_file):
    """
    Validate uploaded files for security and size constraints.
    
    Args:
        uploaded_file: Django UploadedFile object
        
    Raises:
        ValidationError: If file doesn't meet security requirements
    """
    # Check file size
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError(
            f'File size ({uploaded_file.size} bytes) exceeds maximum allowed size '
            f'({settings.MAX_UPLOAD_SIZE} bytes).'
        )
    
    # Check file extension
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    if file_extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError(
            f'File type "{file_extension}" is not allowed. '
            f'Allowed types: {", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)}'
        )
    
    # Check for potentially dangerous file names
    dangerous_names = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    if any(char in uploaded_file.name for char in dangerous_names):
        raise ValidationError('File name contains invalid characters.')
    
    return True


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and other security issues.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove directory path components
    filename = os.path.basename(filename)
    
    # Replace dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limit filename length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    
    return filename


def get_upload_path(instance, filename):
    """
    Generate secure upload path for files.
    
    Args:
        instance: Model instance
        filename: Original filename
        
    Returns:
        str: Secure upload path
    """
    # Sanitize filename
    filename = sanitize_filename(filename)
    
    # Create path based on model and date
    model_name = instance.__class__.__name__.lower()
    date_path = instance.created_at.strftime('%Y/%m/%d') if hasattr(instance, 'created_at') else ''
    
    return f'{model_name}/{date_path}/{filename}'