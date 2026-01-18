"""
URL configuration for hostel_pulse project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('', views.login_page, name='login_page'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('auth/', include('social_django.urls', namespace='social')),
    
    # Pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vibe-map/', views.vibe_map, name='vibe_map'),
    path('rewards/', views.rewards, name='rewards'),
    path('settings/', views.settings_page, name='settings_page'),
    path('home/', views.home, name='home'),  # Redirect to dashboard
    
    # API Endpoints
    path('api/change-mood/', views.change_mood, name='change_mood'),
    path('api/sync/', views.sync_data, name='sync_data'),
    path('api/toggle-theme/', views.toggle_theme, name='toggle_theme'),
]
