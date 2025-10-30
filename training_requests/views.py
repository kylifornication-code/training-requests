from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth, TruncYear
import json
import csv
import logging
from datetime import datetime, timedelta

from .models import TrainingRequest
from .forms import TrainingRequestForm, RequestFilterForm, RequestCompletionForm, CompletedTrainingFilterForm
from accounts.decorators import leadership_required, RoleRequiredMixin, LeadershipRequiredMixin
from accounts.models import UserProfile
from notifications.services import send_teams_notification

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """Enhanced dashboard view for team members showing their training requests"""
    user_role = getattr(request.user.userprofile, 'role', 'TEAM_MEMBER')
    
    # Get user's training requests
    user_requests = TrainingRequest.objects.filter(requester=request.user).select_related('reviewer')
    
    # Apply search and status filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    filtered_requests = user_requests
    if search_query:
        filtered_requests = filtered_requests.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if status_filter:
        filtered_requests = filtered_requests.filter(status=status_filter)
    
    # Paginate recent requests (show 5 per page on dashboard)
    paginator = Paginator(filtered_requests.order_by('-created_at'), 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    stats = {
        'total_requests': user_requests.count(),
        'pending_requests': user_requests.filter(status='PENDING').count(),
        'approved_requests': user_requests.filter(status='APPROVED').count(),
        'completed_requests': user_requests.filter(status='COMPLETED').count(),
    }
    
    # Calculate completion percentage
    if stats['total_requests'] > 0:
        stats['completion_percentage'] = round(
            (stats['completed_requests'] / stats['total_requests']) * 100, 1
        )
    else:
        stats['completion_percentage'] = 0
    
    # Calculate total cost of approved/completed requests
    approved_completed_requests = user_requests.filter(status__in=['APPROVED', 'COMPLETED'])
    total_cost = sum(req.estimated_cost for req in approved_completed_requests)
    stats['total_cost'] = f"${total_cost:,.2f}"
    
    # Get pending count for leadership
    pending_count = 0
    if user_role in ['LEADERSHIP', 'ADMIN']:
        pending_count = TrainingRequest.objects.filter(status='PENDING').count()
    
    context = {
        'user': request.user,
        'user_role': user_role,
        'recent_requests': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'stats': stats,
        'pending_count': pending_count,
        'status_choices': TrainingRequest.STATUS_CHOICES,
        'current_filters': {
            'search': search_query,
            'status': status_filter,
        },
    }
    return render(request, 'dashboard.html', context)


class TrainingRequestCreateView(LoginRequiredMixin, CreateView):
    """View for team members to submit new training requests"""
    model = TrainingRequest
    form_class = TrainingRequestForm
    template_name = 'training_requests/create_request.html'
    success_url = reverse_lazy('training_requests:request_list')
    
    def form_valid(self, form):
        # Set the requester to the current user
        form.instance.requester = self.request.user
        form.instance.status = 'PENDING'
        
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            f'Training request "{form.instance.title}" has been submitted successfully. '
            f'Request ID: {form.instance.id}'
        )
        
        # Send notification to leadership team
        try:
            send_teams_notification(form.instance, 'REQUEST_SUBMITTED')
        except Exception as e:
            # Log error but don't fail the request submission
            logger.error(f"Failed to send Teams notification for request {form.instance.id}: {str(e)}")
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Submit New Training Request'
        return context


class TrainingRequestListView(LoginRequiredMixin, ListView):
    """View for displaying training requests with filtering and pagination"""
    model = TrainingRequest
    template_name = 'training_requests/request_list.html'
    context_object_name = 'requests'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = TrainingRequest.objects.select_related('requester', 'reviewer')
        
        # Filter based on user role
        user_role = getattr(self.request.user.userprofile, 'role', 'TEAM_MEMBER')
        
        if user_role == 'TEAM_MEMBER':
            # Team members see only their own requests
            queryset = queryset.filter(requester=self.request.user)
        # Leadership and admin see all requests (no additional filtering)
        
        # Apply search filters
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(requester__username__icontains=search_query) |
                Q(requester__first_name__icontains=search_query) |
                Q(requester__last_name__icontains=search_query)
            )
        
        # Apply status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Apply training type filter
        type_filter = self.request.GET.get('training_type', '')
        if type_filter:
            queryset = queryset.filter(training_type=type_filter)
        
        # Apply date range filter
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_role = getattr(self.request.user.userprofile, 'role', 'TEAM_MEMBER')
        context['user_role'] = user_role
        context['is_leadership'] = user_role in ['LEADERSHIP', 'ADMIN']
        
        # Add filter choices for the template
        context['status_choices'] = TrainingRequest.STATUS_CHOICES
        context['training_type_choices'] = TrainingRequest.TRAINING_TYPE_CHOICES
        
        # Preserve current filter values
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'status': self.request.GET.get('status', ''),
            'training_type': self.request.GET.get('training_type', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        
        if user_role == 'TEAM_MEMBER':
            context['page_title'] = 'My Training Requests'
        else:
            context['page_title'] = 'All Training Requests'
        
        return context


class TrainingRequestDetailView(LoginRequiredMixin, DetailView):
    """View for displaying detailed information about a training request"""
    model = TrainingRequest
    template_name = 'training_requests/request_detail.html'
    context_object_name = 'request'
    
    def get_queryset(self):
        queryset = TrainingRequest.objects.select_related('requester', 'reviewer')
        
        # Team members can only view their own requests
        user_role = getattr(self.request.user.userprofile, 'role', 'TEAM_MEMBER')
        if user_role == 'TEAM_MEMBER':
            queryset = queryset.filter(requester=self.request.user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_role = getattr(self.request.user.userprofile, 'role', 'TEAM_MEMBER')
        context['user_role'] = user_role
        context['is_leadership'] = user_role in ['LEADERSHIP', 'ADMIN']
        context['can_approve'] = (
            user_role in ['LEADERSHIP', 'ADMIN'] and 
            self.object.status == 'PENDING'
        )
        context['can_complete'] = (
            user_role in ['LEADERSHIP', 'ADMIN'] and 
            self.object.status == 'APPROVED'
        )
        
        return context


@leadership_required
@require_POST
def approve_request(request, pk):
    """View for leadership to approve a training request"""
    training_request = get_object_or_404(TrainingRequest, pk=pk)
    
    if training_request.status != 'PENDING':
        messages.error(request, 'This request has already been reviewed.')
        return redirect('training_requests:request_detail', pk=pk)
    
    # Get review comments from POST data
    review_comments = request.POST.get('review_comments', '').strip()
    
    # Update the request
    training_request.status = 'APPROVED'
    training_request.reviewer = request.user
    training_request.review_comments = review_comments
    training_request.reviewed_at = timezone.now()
    training_request.save()
    
    messages.success(
        request, 
        f'Training request "{training_request.title}" has been approved.'
    )
    
    # Send notification about approval
    try:
        send_teams_notification(training_request, 'REQUEST_APPROVED')
    except Exception as e:
        # Log error but don't fail the approval process
        logger.error(f"Failed to send Teams notification for approved request {training_request.id}: {str(e)}")
    
    return redirect('training_requests:request_detail', pk=pk)


@leadership_required
@require_POST
def deny_request(request, pk):
    """View for leadership to deny a training request"""
    training_request = get_object_or_404(TrainingRequest, pk=pk)
    
    if training_request.status != 'PENDING':
        messages.error(request, 'This request has already been reviewed.')
        return redirect('training_requests:request_detail', pk=pk)
    
    # Get review comments from POST data (required for denial)
    review_comments = request.POST.get('review_comments', '').strip()
    
    if not review_comments:
        messages.error(request, 'Justification is required when denying a request.')
        return redirect('training_requests:request_detail', pk=pk)
    
    # Update the request
    training_request.status = 'DENIED'
    training_request.reviewer = request.user
    training_request.review_comments = review_comments
    training_request.reviewed_at = timezone.now()
    training_request.save()
    
    messages.success(
        request, 
        f'Training request "{training_request.title}" has been denied.'
    )
    
    # Send notification about denial
    try:
        send_teams_notification(training_request, 'REQUEST_DENIED')
    except Exception as e:
        # Log error but don't fail the denial process
        logger.error(f"Failed to send Teams notification for denied request {training_request.id}: {str(e)}")
    
    return redirect('training_requests:request_detail', pk=pk)


@leadership_required
def complete_request(request, pk):
    """View for leadership to mark an approved training request as completed"""
    training_request = get_object_or_404(TrainingRequest, pk=pk)
    
    if training_request.status != 'APPROVED':
        messages.error(request, 'Only approved requests can be marked as completed.')
        return redirect('training_requests:request_detail', pk=pk)
    
    if request.method == 'POST':
        form = RequestCompletionForm(request.POST)
        if form.is_valid():
            # Get completion data from form
            completion_date = form.cleaned_data.get('completion_date') or timezone.now().date()
            completion_notes = form.cleaned_data.get('completion_notes', '').strip()
            
            # Update the request
            training_request.status = 'COMPLETED'
            training_request.completion_notes = completion_notes
            training_request.completed_at = timezone.make_aware(
                datetime.combine(completion_date, datetime.min.time())
            )
            training_request.save()
            
            messages.success(
                request, 
                f'Training request "{training_request.title}" has been marked as completed.'
            )
            
            # Send notification about completion
            try:
                send_teams_notification(training_request, 'REQUEST_COMPLETED')
            except Exception as e:
                # Log error but don't fail the completion process
                logger.error(f"Failed to send Teams notification for completed request {training_request.id}: {str(e)}")
            
            return redirect('training_requests:request_detail', pk=pk)
    else:
        form = RequestCompletionForm()
    
    context = {
        'request_obj': training_request,
        'form': form,
    }
    return render(request, 'training_requests/complete_request.html', context)


class PendingRequestsView(LeadershipRequiredMixin, ListView):
    """View for leadership to see pending requests requiring action"""
    model = TrainingRequest
    template_name = 'training_requests/pending_requests.html'
    context_object_name = 'requests'
    paginate_by = 10
    
    def get_queryset(self):
        return TrainingRequest.objects.filter(
            status='PENDING'
        ).select_related('requester').order_by('created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Pending Training Requests'
        context['pending_count'] = self.get_queryset().count()
        return context


class LeadershipDashboardView(LeadershipRequiredMixin, ListView):
    """Enhanced leadership dashboard for managing training requests"""
    model = TrainingRequest
    template_name = 'training_requests/leadership_dashboard.html'
    context_object_name = 'pending_requests'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = TrainingRequest.objects.filter(
            status='PENDING'
        ).select_related('requester').order_by('created_at')
        
        # Apply filters
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(requester__username__icontains=search_query) |
                Q(requester__first_name__icontains=search_query) |
                Q(requester__last_name__icontains=search_query)
            )
        
        training_type = self.request.GET.get('training_type', '')
        if training_type:
            queryset = queryset.filter(training_type=training_type)
        
        cost_range = self.request.GET.get('cost_range', '')
        if cost_range:
            if cost_range == '0-1000':
                queryset = queryset.filter(estimated_cost__lte=1000)
            elif cost_range == '1000-5000':
                queryset = queryset.filter(estimated_cost__gt=1000, estimated_cost__lte=5000)
            elif cost_range == '5000-10000':
                queryset = queryset.filter(estimated_cost__gt=5000, estimated_cost__lte=10000)
            elif cost_range == '10000+':
                queryset = queryset.filter(estimated_cost__gt=10000)
        
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate statistics
        today = timezone.now().date()
        context['pending_count'] = TrainingRequest.objects.filter(status='PENDING').count()
        context['approved_count'] = TrainingRequest.objects.filter(
            status='APPROVED', 
            reviewed_at__date=today
        ).count()
        context['denied_count'] = TrainingRequest.objects.filter(
            status='DENIED', 
            reviewed_at__date=today
        ).count()
        
        # Calculate total pending cost
        pending_requests = TrainingRequest.objects.filter(status='PENDING')
        context['total_pending_cost'] = sum(req.estimated_cost for req in pending_requests)
        
        # Add filter choices
        context['training_type_choices'] = TrainingRequest.TRAINING_TYPE_CHOICES
        
        # Preserve current filter values
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'training_type': self.request.GET.get('training_type', ''),
            'cost_range': self.request.GET.get('cost_range', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        
        return context
    
    def get(self, request, *args, **kwargs):
        # Handle AJAX requests for auto-refresh
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            pending_count = TrainingRequest.objects.filter(status='PENDING').count()
            return JsonResponse({'pending_count': pending_count})
        
        return super().get(request, *args, **kwargs)


@leadership_required
@require_POST
def bulk_action(request):
    """View for handling bulk approve/deny actions on training requests"""
    action = request.POST.get('action')
    selected_requests = request.POST.get('selected_requests', '').split(',')
    review_comments = request.POST.get('review_comments', '').strip()
    
    if not action or not selected_requests or not selected_requests[0]:
        messages.error(request, 'No action or requests selected.')
        return redirect('training_requests:leadership_dashboard')
    
    # Validate that denial requires comments
    if action == 'deny' and not review_comments:
        messages.error(request, 'Comments are required when denying requests.')
        return redirect('training_requests:leadership_dashboard')
    
    try:
        # Get the requests to update
        request_ids = [int(id.strip()) for id in selected_requests if id.strip()]
        requests_to_update = TrainingRequest.objects.filter(
            pk__in=request_ids,
            status='PENDING'
        )
        
        if not requests_to_update.exists():
            messages.error(request, 'No valid pending requests found.')
            return redirect('training_requests:leadership_dashboard')
        
        # Perform bulk action
        updated_count = 0
        for training_request in requests_to_update:
            if action == 'approve':
                training_request.status = 'APPROVED'
            elif action == 'deny':
                training_request.status = 'DENIED'
            else:
                continue
            
            training_request.reviewer = request.user
            training_request.review_comments = review_comments
            training_request.reviewed_at = timezone.now()
            training_request.save()
            updated_count += 1
        
        # Show success message
        action_word = 'approved' if action == 'approve' else 'denied'
        messages.success(
            request,
            f'Successfully {action_word} {updated_count} training request(s).'
        )
        
        # Send notifications for bulk actions
        notification_type = 'REQUEST_APPROVED' if action == 'approve' else 'REQUEST_DENIED'
        for training_request in requests_to_update:
            try:
                send_teams_notification(training_request, notification_type)
            except Exception as e:
                # Log error but don't fail the bulk operation
                logger.error(f"Failed to send Teams notification for bulk {action} request {training_request.id}: {str(e)}")
        
    except (ValueError, TypeError) as e:
        messages.error(request, 'Invalid request data provided.')
    except Exception as e:
        messages.error(request, f'An error occurred while processing requests: {str(e)}')
    
    return redirect('training_requests:leadership_dashboard')


class RequestReviewView(LeadershipRequiredMixin, DetailView):
    """Enhanced view for reviewing training requests with detailed context"""
    model = TrainingRequest
    template_name = 'training_requests/request_review.html'
    context_object_name = 'request'
    
    def get_queryset(self):
        # Only show pending requests for review
        return TrainingRequest.objects.filter(status='PENDING').select_related('requester', 'requester__userprofile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get requester statistics
        requester = self.object.requester
        requester_requests = TrainingRequest.objects.filter(requester=requester)
        
        context['requester_stats'] = {
            'total_requests': requester_requests.count(),
            'approved_requests': requester_requests.filter(status='APPROVED').count(),
            'completed_requests': requester_requests.filter(status='COMPLETED').count(),
            'total_investment': sum(
                req.estimated_cost for req in requester_requests.filter(status__in=['APPROVED', 'COMPLETED'])
            ),
        }
        
        # Get similar requests (same type or similar cost range)
        from decimal import Decimal
        similar_requests = TrainingRequest.objects.filter(
            Q(training_type=self.object.training_type) |
            Q(estimated_cost__range=(
                self.object.estimated_cost * Decimal('0.8'),
                self.object.estimated_cost * Decimal('1.2')
            ))
        ).exclude(pk=self.object.pk).select_related('requester')[:5]
        
        context['similar_requests'] = similar_requests
        
        return context


@leadership_required
def pending_count_api(request):
    """API endpoint for getting current pending request count"""
    pending_count = TrainingRequest.objects.filter(status='PENDING').count()
    return JsonResponse({'pending_count': pending_count})


class TrainingStatisticsView(LeadershipRequiredMixin, ListView):
    """Dashboard view for training completion statistics and analytics"""
    model = TrainingRequest
    template_name = 'training_requests/training_statistics.html'
    context_object_name = 'completed_requests'
    paginate_by = 20
    
    def get_queryset(self):
        return TrainingRequest.objects.filter(
            status='COMPLETED'
        ).select_related('requester').order_by('-completed_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Overall statistics
        all_requests = TrainingRequest.objects.all()
        completed_requests = all_requests.filter(status='COMPLETED')
        
        context['total_requests'] = all_requests.count()
        context['completed_count'] = completed_requests.count()
        context['completion_rate'] = (
            round((context['completed_count'] / context['total_requests']) * 100, 1)
            if context['total_requests'] > 0 else 0
        )
        
        # Cost statistics
        context['total_investment'] = completed_requests.aggregate(
            total=Sum('estimated_cost')
        )['total'] or 0
        
        context['average_cost'] = completed_requests.aggregate(
            avg=Avg('estimated_cost')
        )['avg'] or 0
        
        # Training type breakdown
        context['type_breakdown'] = completed_requests.values('training_type').annotate(
            count=Count('id'),
            total_cost=Sum('estimated_cost')
        ).order_by('-count')
        
        # Monthly completion trends (last 12 months)
        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_data = completed_requests.filter(
            completed_at__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('completed_at')
        ).values('month').annotate(
            count=Count('id'),
            cost=Sum('estimated_cost')
        ).order_by('month')
        
        context['monthly_trends'] = list(monthly_data)
        
        # Top team members by completed training
        context['top_learners'] = completed_requests.values(
            'requester__first_name', 'requester__last_name', 'requester__username'
        ).annotate(
            count=Count('id'),
            total_cost=Sum('estimated_cost')
        ).order_by('-count')[:10]
        
        return context


class CompletedTrainingReportView(LeadershipRequiredMixin, ListView):
    """View for filtering and reporting on completed training"""
    model = TrainingRequest
    template_name = 'training_requests/completed_training_report.html'
    context_object_name = 'completed_requests'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = TrainingRequest.objects.filter(
            status='COMPLETED'
        ).select_related('requester').order_by('-completed_at')
        
        # Apply filters
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(requester__username__icontains=search_query) |
                Q(requester__first_name__icontains=search_query) |
                Q(requester__last_name__icontains=search_query)
            )
        
        team_member = self.request.GET.get('team_member', '')
        if team_member:
            queryset = queryset.filter(
                Q(requester__username__icontains=team_member) |
                Q(requester__first_name__icontains=team_member) |
                Q(requester__last_name__icontains=team_member)
            )
        
        training_type = self.request.GET.get('training_type', '')
        if training_type:
            queryset = queryset.filter(training_type=training_type)
        
        completion_date_from = self.request.GET.get('completion_date_from', '')
        completion_date_to = self.request.GET.get('completion_date_to', '')
        if completion_date_from:
            queryset = queryset.filter(completed_at__date__gte=completion_date_from)
        if completion_date_to:
            queryset = queryset.filter(completed_at__date__lte=completion_date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter form
        context['filter_form'] = CompletedTrainingFilterForm(self.request.GET)
        
        # Calculate filtered statistics
        filtered_requests = self.get_queryset()
        context['filtered_count'] = filtered_requests.count()
        context['filtered_total_cost'] = filtered_requests.aggregate(
            total=Sum('estimated_cost')
        )['total'] or 0
        
        # Preserve current filter values
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'team_member': self.request.GET.get('team_member', ''),
            'training_type': self.request.GET.get('training_type', ''),
            'completion_date_from': self.request.GET.get('completion_date_from', ''),
            'completion_date_to': self.request.GET.get('completion_date_to', ''),
        }
        
        return context


@leadership_required
def export_completed_training_csv(request):
    """Export completed training data as CSV"""
    # Get the same queryset as the report view with filters
    queryset = TrainingRequest.objects.filter(
        status='COMPLETED'
    ).select_related('requester').order_by('-completed_at')
    
    # Apply the same filters as the report view
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(requester__username__icontains=search_query) |
            Q(requester__first_name__icontains=search_query) |
            Q(requester__last_name__icontains=search_query)
        )
    
    team_member = request.GET.get('team_member', '')
    if team_member:
        queryset = queryset.filter(
            Q(requester__username__icontains=team_member) |
            Q(requester__first_name__icontains=team_member) |
            Q(requester__last_name__icontains=team_member)
        )
    
    training_type = request.GET.get('training_type', '')
    if training_type:
        queryset = queryset.filter(training_type=training_type)
    
    completion_date_from = request.GET.get('completion_date_from', '')
    completion_date_to = request.GET.get('completion_date_to', '')
    if completion_date_from:
        queryset = queryset.filter(completed_at__date__gte=completion_date_from)
    if completion_date_to:
        queryset = queryset.filter(completed_at__date__lte=completion_date_to)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="completed_training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Request ID',
        'Title',
        'Team Member',
        'Training Type',
        'Cost',
        'Currency',
        'Start Date',
        'End Date',
        'Completed Date',
        'Completion Notes',
        'Submitted Date'
    ])
    
    # Write data rows
    for request_obj in queryset:
        writer.writerow([
            request_obj.id,
            request_obj.title,
            request_obj.requester.get_full_name() or request_obj.requester.username,
            request_obj.get_training_type_display(),
            request_obj.estimated_cost,
            request_obj.currency,
            request_obj.start_date.strftime('%Y-%m-%d') if request_obj.start_date else '',
            request_obj.end_date.strftime('%Y-%m-%d') if request_obj.end_date else '',
            request_obj.completed_at.strftime('%Y-%m-%d') if request_obj.completed_at else '',
            request_obj.completion_notes,
            request_obj.created_at.strftime('%Y-%m-%d') if request_obj.created_at else ''
        ])
    
    return response


@leadership_required
def export_completed_training_pdf(request):
    """Export completed training data as PDF"""
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    
    # Get the same queryset as the CSV export with filters
    queryset = TrainingRequest.objects.filter(
        status='COMPLETED'
    ).select_related('requester').order_by('-completed_at')
    
    # Apply the same filters as the report view
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(requester__username__icontains=search_query) |
            Q(requester__first_name__icontains=search_query) |
            Q(requester__last_name__icontains=search_query)
        )
    
    team_member = request.GET.get('team_member', '')
    if team_member:
        queryset = queryset.filter(
            Q(requester__username__icontains=team_member) |
            Q(requester__first_name__icontains=team_member) |
            Q(requester__last_name__icontains=team_member)
        )
    
    training_type = request.GET.get('training_type', '')
    if training_type:
        queryset = queryset.filter(training_type=training_type)
    
    completion_date_from = request.GET.get('completion_date_from', '')
    completion_date_to = request.GET.get('completion_date_to', '')
    if completion_date_from:
        queryset = queryset.filter(completed_at__date__gte=completion_date_from)
    if completion_date_to:
        queryset = queryset.filter(completed_at__date__lte=completion_date_to)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="completed_training_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # Create the PDF object
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1  # Center alignment
    )
    
    # Add title
    title = Paragraph("Completed Training Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Add generation date and filters
    date_para = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal'])
    elements.append(date_para)
    
    # Add filter information if any
    filters_applied = []
    if search_query:
        filters_applied.append(f"Search: {search_query}")
    if team_member:
        filters_applied.append(f"Team Member: {team_member}")
    if training_type:
        type_display = dict(TrainingRequest.TRAINING_TYPE_CHOICES).get(training_type, training_type)
        filters_applied.append(f"Type: {type_display}")
    if completion_date_from:
        filters_applied.append(f"From: {completion_date_from}")
    if completion_date_to:
        filters_applied.append(f"To: {completion_date_to}")
    
    if filters_applied:
        filters_para = Paragraph(f"Filters Applied: {', '.join(filters_applied)}", styles['Normal'])
        elements.append(filters_para)
    
    elements.append(Spacer(1, 20))
    
    # Summary statistics
    total_count = queryset.count()
    total_cost = queryset.aggregate(total=Sum('estimated_cost'))['total'] or 0
    avg_cost = queryset.aggregate(avg=Avg('estimated_cost'))['avg'] or 0
    
    summary_data = [
        ['Summary Statistics', ''],
        ['Total Completed Training', str(total_count)],
        ['Total Investment', f'${total_cost:,.2f}'],
        ['Average Cost per Training', f'${avg_cost:,.2f}'],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Training records table
    if queryset.exists():
        # Limit to first 50 records for PDF readability
        limited_queryset = queryset[:50]
        
        table_data = [['Title', 'Team Member', 'Type', 'Cost', 'Completed Date']]
        
        for request_obj in limited_queryset:
            table_data.append([
                request_obj.title[:30] + ('...' if len(request_obj.title) > 30 else ''),
                request_obj.requester.get_full_name() or request_obj.requester.username,
                request_obj.get_training_type_display(),
                f'{request_obj.currency} {request_obj.estimated_cost}',
                request_obj.completed_at.strftime('%Y-%m-%d') if request_obj.completed_at else ''
            ])
        
        # Create table with appropriate column widths
        col_widths = [2.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch]
        records_table = Table(table_data, colWidths=col_widths)
        records_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(Paragraph("Training Records", styles['Heading2']))
        elements.append(records_table)
        
        if queryset.count() > 50:
            note_para = Paragraph(f"Note: Showing first 50 of {queryset.count()} records. Use CSV export for complete data.", styles['Normal'])
            elements.append(Spacer(1, 12))
            elements.append(note_para)
    else:
        no_data_para = Paragraph("No completed training records found matching the specified criteria.", styles['Normal'])
        elements.append(no_data_para)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response
