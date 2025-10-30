from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncYear, TruncQuarter
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView
from datetime import datetime, timedelta
import json
import csv
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

from training_requests.models import TrainingRequest
from accounts.models import UserProfile
from accounts.decorators import leadership_required, LeadershipRequiredMixin


class AnalyticsDashboardView(LeadershipRequiredMixin, TemplateView):
    """Enhanced analytics dashboard with comprehensive statistics and charts"""
    template_name = 'reports/analytics_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date range filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        # Base queryset
        queryset = TrainingRequest.objects.all()
        
        # Apply date filters
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        # Overall statistics
        context['total_requests'] = queryset.count()
        context['pending_requests'] = queryset.filter(status='PENDING').count()
        context['approved_requests'] = queryset.filter(status='APPROVED').count()
        context['denied_requests'] = queryset.filter(status='DENIED').count()
        context['completed_requests'] = queryset.filter(status='COMPLETED').count()
        
        # Budget analysis
        approved_completed = queryset.filter(status__in=['APPROVED', 'COMPLETED'])
        context['total_budget_allocated'] = approved_completed.aggregate(
            total=Sum('estimated_cost')
        )['total'] or 0
        
        context['average_request_cost'] = approved_completed.aggregate(
            avg=Avg('estimated_cost')
        )['avg'] or 0
        
        context['pending_budget'] = queryset.filter(status='PENDING').aggregate(
            total=Sum('estimated_cost')
        )['total'] or 0
        
        # Training type analysis
        context['training_type_stats'] = queryset.values('training_type').annotate(
            count=Count('id'),
            total_cost=Sum('estimated_cost'),
            avg_cost=Avg('estimated_cost'),
            approved_count=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED']))
        ).order_by('-count')
        
        # Monthly trends (last 12 months)
        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_trends = queryset.filter(
            created_at__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_requests=Count('id'),
            approved_requests=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
            total_cost=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
            avg_cost=Avg('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED']))
        ).order_by('month')
        
        context['monthly_trends'] = list(monthly_trends)
        
        # Team member performance
        context['team_performance'] = queryset.values(
            'requester__first_name', 'requester__last_name', 'requester__username'
        ).annotate(
            total_requests=Count('id'),
            approved_requests=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
            completed_requests=Count('id', filter=Q(status='COMPLETED')),
            total_investment=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
            approval_rate=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED'])) * 100.0 / Count('id')
        ).order_by('-total_requests')[:10]
        
        # Quarterly analysis
        current_year = timezone.now().year
        quarterly_data = queryset.filter(
            created_at__year=current_year
        ).annotate(
            quarter=TruncQuarter('created_at')
        ).values('quarter').annotate(
            requests=Count('id'),
            approved=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
            budget=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED']))
        ).order_by('quarter')
        
        context['quarterly_data'] = list(quarterly_data)
        
        # Cost distribution analysis
        cost_ranges = [
            (0, 1000, '$0 - $1,000'),
            (1000, 5000, '$1,000 - $5,000'),
            (5000, 10000, '$5,000 - $10,000'),
            (10000, float('inf'), '$10,000+')
        ]
        
        cost_distribution = []
        for min_cost, max_cost, label in cost_ranges:
            if max_cost == float('inf'):
                count = queryset.filter(estimated_cost__gte=min_cost).count()
                total_cost = queryset.filter(estimated_cost__gte=min_cost).aggregate(
                    total=Sum('estimated_cost')
                )['total'] or 0
            else:
                count = queryset.filter(
                    estimated_cost__gte=min_cost, 
                    estimated_cost__lt=max_cost
                ).count()
                total_cost = queryset.filter(
                    estimated_cost__gte=min_cost, 
                    estimated_cost__lt=max_cost
                ).aggregate(total=Sum('estimated_cost'))['total'] or 0
            
            cost_distribution.append({
                'range': label,
                'count': count,
                'total_cost': total_cost,
                'percentage': round((count / context['total_requests']) * 100, 1) if context['total_requests'] > 0 else 0
            })
        
        context['cost_distribution'] = cost_distribution
        
        # Approval rate by training type
        approval_rates = []
        for training_type, display_name in TrainingRequest.TRAINING_TYPE_CHOICES:
            type_requests = queryset.filter(training_type=training_type)
            total = type_requests.count()
            approved = type_requests.filter(status__in=['APPROVED', 'COMPLETED']).count()
            
            if total > 0:
                approval_rates.append({
                    'type': display_name,
                    'total': total,
                    'approved': approved,
                    'rate': round((approved / total) * 100, 1)
                })
        
        context['approval_rates'] = approval_rates
        
        # Current filters
        context['current_filters'] = {
            'date_from': date_from,
            'date_to': date_to,
        }
        
        return context


@leadership_required
def budget_analysis_api(request):
    """API endpoint for budget analysis data for charts"""
    # Get date range from request
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    queryset = TrainingRequest.objects.all()
    
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    
    # Monthly budget trends
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_budget = queryset.filter(
        created_at__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        requested_budget=Sum('estimated_cost'),
        approved_budget=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED']))
    ).order_by('month')
    
    # Training type budget breakdown
    type_budget = queryset.filter(
        status__in=['APPROVED', 'COMPLETED']
    ).values('training_type').annotate(
        budget=Sum('estimated_cost'),
        count=Count('id')
    ).order_by('-budget')
    
    # Status distribution
    status_data = []
    for status, display_name in TrainingRequest.STATUS_CHOICES:
        count = queryset.filter(status=status).count()
        budget = queryset.filter(status=status).aggregate(
            total=Sum('estimated_cost')
        )['total'] or 0
        
        status_data.append({
            'status': display_name,
            'count': count,
            'budget': float(budget)
        })
    
    return JsonResponse({
        'monthly_budget': [
            {
                'month': item['month'].strftime('%Y-%m'),
                'month_name': item['month'].strftime('%b %Y'),
                'requested': float(item['requested_budget'] or 0),
                'approved': float(item['approved_budget'] or 0)
            }
            for item in monthly_budget
        ],
        'type_budget': [
            {
                'type': dict(TrainingRequest.TRAINING_TYPE_CHOICES)[item['training_type']],
                'budget': float(item['budget']),
                'count': item['count']
            }
            for item in type_budget
        ],
        'status_distribution': status_data
    })


@leadership_required
def team_performance_api(request):
    """API endpoint for team performance data for charts"""
    # Get top 10 team members by various metrics
    queryset = TrainingRequest.objects.all()
    
    # Most active requesters
    most_active = queryset.values(
        'requester__first_name', 'requester__last_name', 'requester__username'
    ).annotate(
        total_requests=Count('id'),
        approved_requests=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
        total_investment=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED']))
    ).order_by('-total_requests')[:10]
    
    # Highest investment
    highest_investment = queryset.filter(
        status__in=['APPROVED', 'COMPLETED']
    ).values(
        'requester__first_name', 'requester__last_name', 'requester__username'
    ).annotate(
        total_investment=Sum('estimated_cost'),
        request_count=Count('id')
    ).order_by('-total_investment')[:10]
    
    def format_name(item):
        if item['requester__first_name'] and item['requester__last_name']:
            return f"{item['requester__first_name']} {item['requester__last_name']}"
        return item['requester__username']
    
    return JsonResponse({
        'most_active': [
            {
                'name': format_name(item),
                'total_requests': item['total_requests'],
                'approved_requests': item['approved_requests'],
                'total_investment': float(item['total_investment'] or 0)
            }
            for item in most_active
        ],
        'highest_investment': [
            {
                'name': format_name(item),
                'total_investment': float(item['total_investment'] or 0),
                'request_count': item['request_count']
            }
            for item in highest_investment
        ]
    })


@leadership_required
def export_analytics_pdf(request):
    """Export analytics report as PDF"""
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="training_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    # Create the PDF object
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add title
    title = Paragraph("Training Request Analytics Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Add generation date
    date_para = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal'])
    elements.append(date_para)
    elements.append(Spacer(1, 20))
    
    # Get data
    queryset = TrainingRequest.objects.all()
    
    # Overall statistics
    stats_data = [
        ['Metric', 'Value'],
        ['Total Requests', str(queryset.count())],
        ['Pending Requests', str(queryset.filter(status='PENDING').count())],
        ['Approved Requests', str(queryset.filter(status='APPROVED').count())],
        ['Completed Requests', str(queryset.filter(status='COMPLETED').count())],
        ['Denied Requests', str(queryset.filter(status='DENIED').count())],
    ]
    
    # Budget statistics
    approved_completed = queryset.filter(status__in=['APPROVED', 'COMPLETED'])
    total_budget = approved_completed.aggregate(total=Sum('estimated_cost'))['total'] or 0
    avg_cost = approved_completed.aggregate(avg=Avg('estimated_cost'))['avg'] or 0
    pending_budget = queryset.filter(status='PENDING').aggregate(total=Sum('estimated_cost'))['total'] or 0
    
    stats_data.extend([
        ['Total Budget Allocated', f'${total_budget:,.2f}'],
        ['Average Request Cost', f'${avg_cost:,.2f}'],
        ['Pending Budget', f'${pending_budget:,.2f}'],
    ])
    
    # Create statistics table
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(Paragraph("Overall Statistics", styles['Heading2']))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # Training type breakdown
    type_stats = queryset.values('training_type').annotate(
        count=Count('id'),
        total_cost=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED']))
    ).order_by('-count')
    
    type_data = [['Training Type', 'Count', 'Total Cost']]
    for item in type_stats:
        type_name = dict(TrainingRequest.TRAINING_TYPE_CHOICES)[item['training_type']]
        cost = item['total_cost'] or 0
        type_data.append([type_name, str(item['count']), f'${cost:,.2f}'])
    
    type_table = Table(type_data)
    type_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(Paragraph("Training Type Breakdown", styles['Heading2']))
    elements.append(type_table)
    elements.append(Spacer(1, 20))
    
    # Team performance
    team_data = [['Team Member', 'Total Requests', 'Approved', 'Total Investment']]
    team_performance = queryset.values(
        'requester__first_name', 'requester__last_name', 'requester__username'
    ).annotate(
        total_requests=Count('id'),
        approved_requests=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
        total_investment=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED']))
    ).order_by('-total_requests')[:10]
    
    for item in team_performance:
        name = f"{item['requester__first_name']} {item['requester__last_name']}" if item['requester__first_name'] else item['requester__username']
        investment = item['total_investment'] or 0
        team_data.append([
            name,
            str(item['total_requests']),
            str(item['approved_requests']),
            f'${investment:,.2f}'
        ])
    
    team_table = Table(team_data)
    team_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(Paragraph("Top Team Members", styles['Heading2']))
    elements.append(team_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@leadership_required
def export_budget_analysis_csv(request):
    """Export budget analysis data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="budget_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header sections
    writer.writerow(['Training Request Budget Analysis Report'])
    writer.writerow([f'Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}'])
    writer.writerow([])  # Empty row
    
    # Overall statistics
    queryset = TrainingRequest.objects.all()
    approved_completed = queryset.filter(status__in=['APPROVED', 'COMPLETED'])
    
    writer.writerow(['OVERALL STATISTICS'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Requests', queryset.count()])
    writer.writerow(['Pending Requests', queryset.filter(status='PENDING').count()])
    writer.writerow(['Approved Requests', queryset.filter(status='APPROVED').count()])
    writer.writerow(['Completed Requests', queryset.filter(status='COMPLETED').count()])
    writer.writerow(['Denied Requests', queryset.filter(status='DENIED').count()])
    writer.writerow(['Total Budget Allocated', f'${(approved_completed.aggregate(total=Sum("estimated_cost"))["total"] or 0):,.2f}'])
    writer.writerow(['Average Request Cost', f'${(approved_completed.aggregate(avg=Avg("estimated_cost"))["avg"] or 0):,.2f}'])
    writer.writerow(['Pending Budget', f'${(queryset.filter(status="PENDING").aggregate(total=Sum("estimated_cost"))["total"] or 0):,.2f}'])
    writer.writerow([])  # Empty row
    
    # Training type breakdown
    writer.writerow(['TRAINING TYPE BREAKDOWN'])
    writer.writerow(['Training Type', 'Count', 'Total Cost', 'Average Cost', 'Approved Count'])
    
    type_stats = queryset.values('training_type').annotate(
        count=Count('id'),
        total_cost=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
        avg_cost=Avg('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
        approved_count=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED']))
    ).order_by('-count')
    
    for item in type_stats:
        type_name = dict(TrainingRequest.TRAINING_TYPE_CHOICES)[item['training_type']]
        writer.writerow([
            type_name,
            item['count'],
            f'${(item["total_cost"] or 0):,.2f}',
            f'${(item["avg_cost"] or 0):,.2f}',
            item['approved_count']
        ])
    
    writer.writerow([])  # Empty row
    
    # Monthly trends (last 12 months)
    writer.writerow(['MONTHLY TRENDS (LAST 12 MONTHS)'])
    writer.writerow(['Month', 'Total Requests', 'Approved Requests', 'Total Cost', 'Average Cost'])
    
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_trends = queryset.filter(
        created_at__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_requests=Count('id'),
        approved_requests=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
        total_cost=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
        avg_cost=Avg('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED']))
    ).order_by('month')
    
    for item in monthly_trends:
        writer.writerow([
            item['month'].strftime('%B %Y'),
            item['total_requests'],
            item['approved_requests'],
            f'${(item["total_cost"] or 0):,.2f}',
            f'${(item["avg_cost"] or 0):,.2f}'
        ])
    
    writer.writerow([])  # Empty row
    
    # Team performance
    writer.writerow(['TEAM PERFORMANCE'])
    writer.writerow(['Team Member', 'Total Requests', 'Approved Requests', 'Completed Requests', 'Total Investment', 'Approval Rate'])
    
    team_performance = queryset.values(
        'requester__first_name', 'requester__last_name', 'requester__username'
    ).annotate(
        total_requests=Count('id'),
        approved_requests=Count('id', filter=Q(status__in=['APPROVED', 'COMPLETED'])),
        completed_requests=Count('id', filter=Q(status='COMPLETED')),
        total_investment=Sum('estimated_cost', filter=Q(status__in=['APPROVED', 'COMPLETED']))
    ).order_by('-total_requests')
    
    for item in team_performance:
        name = f"{item['requester__first_name']} {item['requester__last_name']}" if item['requester__first_name'] else item['requester__username']
        approval_rate = (item['approved_requests'] / item['total_requests'] * 100) if item['total_requests'] > 0 else 0
        
        writer.writerow([
            name,
            item['total_requests'],
            item['approved_requests'],
            item['completed_requests'],
            f'${(item["total_investment"] or 0):,.2f}',
            f'{approval_rate:.1f}%'
        ])
    
    return response
