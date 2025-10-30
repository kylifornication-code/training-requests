from django.urls import path
from . import views

app_name = 'training_requests'

urlpatterns = [
    # Dashboard - main landing page after login
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='home'),  # Redirect root to dashboard
    
    # Training request management
    path('requests/', views.TrainingRequestListView.as_view(), name='request_list'),
    path('requests/my/', views.TrainingRequestListView.as_view(), name='my_requests'),
    path('requests/new/', views.TrainingRequestCreateView.as_view(), name='create_request'),
    path('requests/<int:pk>/', views.TrainingRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/review/', views.RequestReviewView.as_view(), name='request_review'),
    
    # Leadership actions
    path('requests/<int:pk>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:pk>/deny/', views.deny_request, name='deny_request'),
    path('requests/<int:pk>/complete/', views.complete_request, name='complete_request'),
    
    # Leadership dashboard
    path('pending/', views.PendingRequestsView.as_view(), name='pending_requests'),
    path('leadership/', views.LeadershipDashboardView.as_view(), name='leadership_dashboard'),
    path('bulk-action/', views.bulk_action, name='bulk_action'),
    path('api/pending-count/', views.pending_count_api, name='pending_count_api'),
    
    # Training completion tracking and reporting
    path('statistics/', views.TrainingStatisticsView.as_view(), name='training_statistics'),
    path('completed/', views.CompletedTrainingReportView.as_view(), name='completed_training_report'),
    path('export/completed/', views.export_completed_training_csv, name='export_completed_training'),
    path('export/completed-pdf/', views.export_completed_training_pdf, name='export_completed_training_pdf'),
]