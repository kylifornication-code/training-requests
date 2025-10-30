from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Analytics Dashboard
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    
    # API endpoints for chart data
    path('api/budget-analysis/', views.budget_analysis_api, name='budget_analysis_api'),
    path('api/team-performance/', views.team_performance_api, name='team_performance_api'),
    
    # Export functionality
    path('export/analytics-pdf/', views.export_analytics_pdf, name='export_analytics_pdf'),
    path('export/budget-csv/', views.export_budget_analysis_csv, name='export_budget_analysis_csv'),
]