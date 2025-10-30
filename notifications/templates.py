"""
Notification templates for Microsoft Teams messages.
"""
from typing import Dict
from django.conf import settings
from training_requests.models import TrainingRequest


class NotificationTemplates:
    """Templates for different types of notifications."""
    
    @staticmethod
    def get_base_url() -> str:
        """Get the base URL for generating links."""
        return getattr(settings, 'BASE_URL', 'http://localhost:8000')
    
    @staticmethod
    def get_request_url(request: TrainingRequest) -> str:
        """Generate URL for request details."""
        base_url = NotificationTemplates.get_base_url()
        return f"{base_url}/requests/{request.id}/"
    
    @staticmethod
    def request_submitted_template(request: TrainingRequest) -> Dict:
        """Template for new request submission notification."""
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"New Training Request: {request.title}",
            "themeColor": "0078D4",
            "sections": [
                {
                    "activityTitle": "📋 New Training Request Submitted",
                    "activitySubtitle": f"Request by {request.requester.get_full_name() or request.requester.username}",
                    "activityImage": "https://img.icons8.com/fluency/48/000000/training.png",
                    "facts": [
                        {
                            "name": "Training Title:",
                            "value": request.title
                        },
                        {
                            "name": "Requester:",
                            "value": request.requester.get_full_name() or request.requester.username
                        },
                        {
                            "name": "Type:",
                            "value": request.get_training_type_display()
                        },
                        {
                            "name": "Estimated Cost:",
                            "value": f"{request.currency} {request.estimated_cost:,.2f}"
                        },
                        {
                            "name": "Training Dates:",
                            "value": f"{request.start_date.strftime('%B %d, %Y')} to {request.end_date.strftime('%B %d, %Y')}"
                        },
                        {
                            "name": "Status:",
                            "value": "⏳ Pending Review"
                        }
                    ],
                    "text": f"**Justification:** {request.justification[:300]}{'...' if len(request.justification) > 300 else ''}"
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "Review Request",
                    "targets": [
                        {
                            "os": "default",
                            "uri": NotificationTemplates.get_request_url(request)
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def request_approved_template(request: TrainingRequest) -> Dict:
        """Template for request approval notification."""
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"Training Request Approved: {request.title}",
            "themeColor": "107C10",
            "sections": [
                {
                    "activityTitle": "✅ Training Request Approved",
                    "activitySubtitle": f"Request by {request.requester.get_full_name() or request.requester.username}",
                    "activityImage": "https://img.icons8.com/fluency/48/000000/checkmark.png",
                    "facts": [
                        {
                            "name": "Training Title:",
                            "value": request.title
                        },
                        {
                            "name": "Requester:",
                            "value": request.requester.get_full_name() or request.requester.username
                        },
                        {
                            "name": "Type:",
                            "value": request.get_training_type_display()
                        },
                        {
                            "name": "Approved Cost:",
                            "value": f"{request.currency} {request.estimated_cost:,.2f}"
                        },
                        {
                            "name": "Training Dates:",
                            "value": f"{request.start_date.strftime('%B %d, %Y')} to {request.end_date.strftime('%B %d, %Y')}"
                        },
                        {
                            "name": "Approved by:",
                            "value": request.reviewer.get_full_name() or request.reviewer.username if request.reviewer else "Unknown"
                        },
                        {
                            "name": "Status:",
                            "value": "✅ Approved"
                        }
                    ],
                    "text": f"**Reviewer Comments:** {request.review_comments if request.review_comments else 'No additional comments'}"
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Request Details",
                    "targets": [
                        {
                            "os": "default",
                            "uri": NotificationTemplates.get_request_url(request)
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def request_denied_template(request: TrainingRequest) -> Dict:
        """Template for request denial notification."""
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"Training Request Denied: {request.title}",
            "themeColor": "D13438",
            "sections": [
                {
                    "activityTitle": "❌ Training Request Denied",
                    "activitySubtitle": f"Request by {request.requester.get_full_name() or request.requester.username}",
                    "activityImage": "https://img.icons8.com/fluency/48/000000/cancel.png",
                    "facts": [
                        {
                            "name": "Training Title:",
                            "value": request.title
                        },
                        {
                            "name": "Requester:",
                            "value": request.requester.get_full_name() or request.requester.username
                        },
                        {
                            "name": "Type:",
                            "value": request.get_training_type_display()
                        },
                        {
                            "name": "Requested Cost:",
                            "value": f"{request.currency} {request.estimated_cost:,.2f}"
                        },
                        {
                            "name": "Training Dates:",
                            "value": f"{request.start_date.strftime('%B %d, %Y')} to {request.end_date.strftime('%B %d, %Y')}"
                        },
                        {
                            "name": "Reviewed by:",
                            "value": request.reviewer.get_full_name() or request.reviewer.username if request.reviewer else "Unknown"
                        },
                        {
                            "name": "Status:",
                            "value": "❌ Denied"
                        }
                    ],
                    "text": f"**Reason for Denial:** {request.review_comments if request.review_comments else 'No reason provided'}"
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Request Details",
                    "targets": [
                        {
                            "os": "default",
                            "uri": NotificationTemplates.get_request_url(request)
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def request_completed_template(request: TrainingRequest) -> Dict:
        """Template for request completion notification."""
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"Training Completed: {request.title}",
            "themeColor": "8764B8",
            "sections": [
                {
                    "activityTitle": "🎓 Training Request Completed",
                    "activitySubtitle": f"Training completed by {request.requester.get_full_name() or request.requester.username}",
                    "activityImage": "https://img.icons8.com/fluency/48/000000/graduation-cap.png",
                    "facts": [
                        {
                            "name": "Training Title:",
                            "value": request.title
                        },
                        {
                            "name": "Participant:",
                            "value": request.requester.get_full_name() or request.requester.username
                        },
                        {
                            "name": "Type:",
                            "value": request.get_training_type_display()
                        },
                        {
                            "name": "Final Cost:",
                            "value": f"{request.currency} {request.estimated_cost:,.2f}"
                        },
                        {
                            "name": "Training Dates:",
                            "value": f"{request.start_date.strftime('%B %d, %Y')} to {request.end_date.strftime('%B %d, %Y')}"
                        },
                        {
                            "name": "Completed:",
                            "value": request.completed_at.strftime('%B %d, %Y at %I:%M %p') if request.completed_at else "Recently"
                        },
                        {
                            "name": "Status:",
                            "value": "🎓 Completed"
                        }
                    ],
                    "text": f"**Completion Notes:** {request.completion_notes if request.completion_notes else 'Training completed successfully'}"
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Request Details",
                    "targets": [
                        {
                            "os": "default",
                            "uri": NotificationTemplates.get_request_url(request)
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def get_template(notification_type: str, request: TrainingRequest) -> Dict:
        """
        Get the appropriate template for the notification type.
        
        Args:
            notification_type: Type of notification
            request: TrainingRequest instance
            
        Returns:
            Dictionary containing the Teams message template
        """
        template_map = {
            'REQUEST_SUBMITTED': NotificationTemplates.request_submitted_template,
            'REQUEST_APPROVED': NotificationTemplates.request_approved_template,
            'REQUEST_DENIED': NotificationTemplates.request_denied_template,
            'REQUEST_COMPLETED': NotificationTemplates.request_completed_template,
        }
        
        template_func = template_map.get(notification_type)
        if template_func:
            return template_func(request)
        else:
            # Fallback to basic template
            return NotificationTemplates.request_submitted_template(request)