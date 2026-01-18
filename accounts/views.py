from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json


def login_page(request):
    """Landing page with Google OAuth sign-in"""
    return render(request, 'landing.html')


@login_required
def permission_screen(request):
    """Permission request screen"""
    return render(request, 'permissions.html')


@login_required
def dashboard(request):
    """Main dashboard with wellness tracking"""
    from .gemini_service import generate_wellness_suggestions, get_mood_message
    from .data_sync_service import get_user_dashboard_data, sync_user_data
    
    # Get real data from MongoDB
    dashboard_data = get_user_dashboard_data(request.user)
    today_data = dashboard_data.get('today') if dashboard_data else None
    
    # If no data exists, auto-sync on first visit
    if not today_data:
        # Try to sync automatically
        try:
            wellness_data = sync_user_data(request.user)
            if wellness_data:
                # Refresh dashboard data after sync
                dashboard_data = get_user_dashboard_data(request.user)
                today_data = dashboard_data.get('today')
        except Exception as e:
            print(f"Auto-sync error: {e}")
    
    # If still no data after auto-sync, show message
    if not today_data:
        context = {
            'no_data': True,
            'message': 'Unable to sync data automatically. Click "Sync My Life" to try again.',
            'mood': 'balanced',
            'balance_score': 50,
            'suggestions': [
                'Make sure Google Fit is installed and tracking data',
                'Add classes to your Google Calendar',
                'Click "Sync My Life" to refresh'
            ]
        }
        return render(request, 'dashboard.html', context)
    
    # Get mood from session, default to 'balanced'
    mood = request.session.get('mood', 'balanced')
    balance_score = today_data.get('balance_score', 50)
    
    # Check if we need to regenerate suggestions
    cached_mood = request.session.get('cached_mood')
    force_regenerate = request.session.get('force_regenerate', False)
    
    if not request.session.get('suggestions') or cached_mood != mood or force_regenerate:
        user_name = request.user.get_full_name() or request.user.username or "Student"
        
        # Prepare detailed wellness context for Gemini
        wellness_context = {
            'sleep_hours': today_data.get('sleep_hours'),
            'sleep_quality': today_data.get('sleep_quality'),
            'step_count': today_data.get('step_count', 0),
            'active_minutes': today_data.get('active_minutes', 0),
            'classes_attended': today_data.get('classes_attended', 0),
            'classes_total': today_data.get('classes_total', 0),
        }
        
        # Generate personalized suggestions with real data
        suggestions = generate_wellness_suggestions(mood, balance_score, user_name, wellness_context)
        request.session['suggestions'] = suggestions
        request.session['cached_mood'] = mood
        request.session['force_regenerate'] = False
    else:
        suggestions = request.session.get('suggestions')
    
    context = {
        'mood': mood,
        'balance_score': balance_score,
        'message': get_mood_message(mood),
        'suggestions': suggestions,
        'sleep_hours': today_data.get('sleep_hours'),
        'sleep_quality': today_data.get('sleep_quality'),
        'step_count': today_data.get('step_count', 0),
        'active_minutes': today_data.get('active_minutes', 0),
        'classes_attended': today_data.get('classes_attended', 0),
        'classes_total': today_data.get('classes_total', 0),
        'history': dashboard_data.get('history', []),
        'last_sync': today_data.get('updated_at')
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def vibe_map(request):
    """Hostel vibe map showing zone activity"""
    zones = [
        {'name': 'Common Room', 'vibe': 'Active', 'color': 'green', 'emoji': '🟢'},
        {'name': 'Library', 'vibe': 'Quiet & Focused', 'color': 'blue', 'emoji': '🔵'},
        {'name': 'Cafeteria', 'vibe': 'Moderate', 'color': 'yellow', 'emoji': '🟡'}
    ]
    
    context = {'zones': zones}
    return render(request, 'vibe_map.html', context)


@login_required
def rewards(request):
    """Rewards page with achievements and streaks"""
    from .mongodb_models import get_user_achievements, initialize_user_achievements
    from .data_sync_service import get_user_dashboard_data
    
    # Initialize achievements if they don't exist
    initialize_user_achievements(request.user.id)
    
    # Get dashboard data
    dashboard_data = get_user_dashboard_data(request.user)
    
    # Handle case when no data exists yet
    if not dashboard_data or not dashboard_data.get('achievements'):
        achievements_data = []
    else:
        achievements_data = dashboard_data.get('achievements', [])
    
    streak_data = dashboard_data.get('streak') if dashboard_data else None
    
    # Calculate progress bar from recent history
    history = dashboard_data.get('history', []) if dashboard_data else []
    if history:
        avg_score = sum(day.get('balance_score', 0) for day in history[:7]) / min(len(history), 7)
        progress_bar = int(avg_score)
    else:
        progress_bar = 0
    
    context = {
        'daily_streak': streak_data.get('current_streak', 0) if streak_data else 0,
        'progress_bar': progress_bar,
        'achievements': achievements_data
    }
    
    return render(request, 'rewards.html', context)


@login_required
def settings_page(request):
    """Settings page with about and support info"""
    return render(request, 'settings.html')


@login_required
def home(request):
    """Redirect old home route to dashboard"""
    return redirect('dashboard')


def logout_view(request):
    """Logout and redirect to landing page"""
    logout(request)
    return redirect('login_page')


# API Endpoints
@login_required
def change_mood(request):
    """API endpoint to change user mood"""
    if request.method == 'POST':
        data = json.loads(request.body)
        mood = data.get('mood', 'balanced')
        request.session['mood'] = mood
        request.session['force_regenerate'] = True
        return JsonResponse({'success': True, 'mood': mood})
    return JsonResponse({'success': False})


@login_required
def sync_data(request):
    """API endpoint to sync wellness data from Google APIs"""
    from .data_sync_service import sync_user_data
    
    if request.method == 'POST':
        try:
            # Sync real data from Google Fit and Calendar
            wellness_data = sync_user_data(request.user)
            
            if wellness_data:
                request.session['force_regenerate'] = True
                return JsonResponse({
                    'success': True,
                    'balance_score': wellness_data.get('balance_score', 50),
                    'message': 'Data synced successfully!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Unable to sync data. Please check your Google Fit and Calendar permissions.'
                })
        except Exception as e:
            print(f"Sync error: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Sync failed: {str(e)}'
            })
    return JsonResponse({'success': False})


def toggle_theme(request):
    """API endpoint to toggle theme"""
    if request.method == 'POST':
        data = json.loads(request.body)
        theme = data.get('theme', 'light')
        request.session['theme'] = theme
        return JsonResponse({'success': True, 'theme': theme})
    return JsonResponse({'success': False})
