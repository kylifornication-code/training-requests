"""
Custom error views and health check for the training system application.
"""
from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden, JsonResponse
from django.db import connection
from django.conf import settings
import time


def handler404(request, exception):
    """
    Custom 404 error handler.
    """
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """
    Custom 500 error handler.
    """
    return render(request, 'errors/500.html', status=500)


def handler403(request, exception):
    """
    Custom 403 error handler.
    """
    return render(request, 'errors/403.html', status=403)


def health_check(request):
    """
    Health check endpoint for production monitoring.
    Returns JSON with system status information.
    """
    start_time = time.time()
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Calculate response time
    response_time = round((time.time() - start_time) * 1000, 2)  # in milliseconds
    
    # Determine overall status
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    
    health_data = {
        "status": overall_status,
        "timestamp": int(time.time()),
        "response_time_ms": response_time,
        "checks": {
            "database": db_status,
            "django": "healthy"
        },
        "version": getattr(settings, 'VERSION', '1.0.0')
    }
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_status == "healthy" else 503
    
    return JsonResponse(health_data, status=status_code)