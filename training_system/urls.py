"""
URL configuration for training_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views

# Custom error handlers
handler404 = 'training_system.views.handler404'
handler500 = 'training_system.views.handler500'
handler403 = 'training_system.views.handler403'

urlpatterns = [
    # Health check endpoint for production monitoring
    path('health/', views.health_check, name='health_check'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Application URLs
    path('', include('accounts.urls')),
    path('', include('training_requests.urls')),
    path('reports/', include('reports.urls')),
    path('notifications/', include('notifications.urls')),
    
    # Favicon redirect to prevent 404s
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    
    # Add debug toolbar if available
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
