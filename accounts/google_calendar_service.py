"""
Google Calendar API Service for collecting class/study schedule data
"""
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from social_django.models import UserSocialAuth
import re


def get_google_credentials(user):
    """Get Google OAuth credentials for the user"""
    try:
        social_auth = UserSocialAuth.objects.get(user=user, provider='google-oauth2')
        access_token = social_auth.extra_data.get('access_token')
        refresh_token = social_auth.extra_data.get('refresh_token')
        
        if not access_token:
            return None
        
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=social_auth.extra_data.get('client_id'),
            client_secret=social_auth.extra_data.get('client_secret'),
        )
        
        return credentials
    except UserSocialAuth.DoesNotExist:
        return None


def get_todays_events(user, date=None):
    """
    Get today's calendar events
    
    Args:
        user: Django user object
        date: datetime object (defaults to today)
    
    Returns:
        list: List of calendar events
    """
    credentials = get_google_credentials(user)
    if not credentials:
        return []
    
    try:
        service = build('calendar', 'v3', credentials=credentials)
        
        if date is None:
            date = datetime.now()
        
        # Set time range for the day
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        # Get events from primary calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat() + 'Z',
            timeMax=end_time.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
        
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return []


def identify_class_events(events):
    """
    Filter calendar events to identify class/study events
    
    Args:
        events: List of calendar events
    
    Returns:
        list: Filtered list of class events
    """
    # Keywords that indicate class/study events
    class_keywords = [
        'class', 'lecture', 'lab', 'tutorial', 'seminar', 'workshop',
        'study', 'exam', 'test', 'quiz', 'assignment', 'project',
        'course', 'lesson', 'training', 'session', 'meeting'
    ]
    
    class_events = []
    
    for event in events:
        summary = event.get('summary', '').lower()
        description = event.get('description', '').lower()
        
        # Check if any keyword is in the event title or description
        is_class = any(keyword in summary or keyword in description for keyword in class_keywords)
        
        if is_class:
            class_events.append(event)
    
    return class_events


def calculate_attendance(user, date=None):
    """
    Calculate class attendance for a specific date
    
    Args:
        user: Django user object
        date: datetime object (defaults to today)
    
    Returns:
        dict: {
            'classes_total': int,
            'classes_attended': int,
            'attendance_rate': float,
            'class_list': list
        }
    """
    events = get_todays_events(user, date)
    class_events = identify_class_events(events)
    
    total_classes = len(class_events)
    
    # For now, we'll assume all scheduled classes are attended
    # In a real implementation, you might track actual attendance
    attended_classes = total_classes
    
    attendance_rate = (attended_classes / total_classes * 100) if total_classes > 0 else 0
    
    # Extract class information
    class_list = []
    for event in class_events:
        start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
        end = event.get('end', {}).get('dateTime', event.get('end', {}).get('date'))
        
        class_list.append({
            'title': event.get('summary', 'Untitled'),
            'start_time': start,
            'end_time': end,
            'location': event.get('location', ''),
            'attended': True  # Default to attended
        })
    
    return {
        'classes_total': total_classes,
        'classes_attended': attended_classes,
        'attendance_rate': round(attendance_rate, 1),
        'class_list': class_list
    }


def get_weekly_schedule(user):
    """
    Get the weekly class schedule
    
    Args:
        user: Django user object
    
    Returns:
        dict: Weekly schedule data
    """
    today = datetime.now()
    weekly_data = []
    
    for i in range(7):
        date = today - timedelta(days=i)
        attendance = calculate_attendance(user, date)
        weekly_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'day': date.strftime('%A'),
            'attendance': attendance
        })
    
    return weekly_data
