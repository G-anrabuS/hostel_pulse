"""
Google Fit API Service for collecting health and fitness data
"""
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from social_django.models import UserSocialAuth


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


def get_sleep_data(user, date=None):
    """
    Get sleep data from Google Fit for a specific date
    
    Args:
        user: Django user object
        date: datetime object (defaults to today)
    
    Returns:
        dict: {
            'sleep_hours': float,
            'sleep_quality': str ('good', 'fair', 'poor'),
            'bedtime': str,
            'waketime': str
        }
    """
    credentials = get_google_credentials(user)
    if not credentials:
        return None
    
    try:
        service = build('fitness', 'v1', credentials=credentials)
        
        if date is None:
            date = datetime.now()
        
        # Set time range for the previous night (6 PM yesterday to 12 PM today)
        start_time = datetime.combine(date - timedelta(days=1), datetime.min.time().replace(hour=18))
        end_time = datetime.combine(date, datetime.min.time().replace(hour=12))
        
        start_nanos = int(start_time.timestamp() * 1e9)
        end_nanos = int(end_time.timestamp() * 1e9)
        
        # Request sleep session data
        dataset_id = f"{start_nanos}-{end_nanos}"
        
        # Get sleep sessions
        sessions_response = service.users().sessions().list(
            userId='me',
            startTime=start_time.isoformat() + 'Z',
            endTime=end_time.isoformat() + 'Z',
            activityType=72  # Sleep activity type
        ).execute()
        
        sessions = sessions_response.get('session', [])
        
        if not sessions:
            # Fallback: try to get sleep data from data sources
            datasources = service.users().dataSources().list(
                userId='me',
                dataTypeName='com.google.sleep.segment'
            ).execute()
            
            if datasources.get('dataSource'):
                # Get sleep segments
                data_source_id = datasources['dataSource'][0]['dataStreamId']
                dataset = service.users().dataSources().datasets().get(
                    userId='me',
                    dataSourceId=data_source_id,
                    datasetId=dataset_id
                ).execute()
                
                points = dataset.get('point', [])
                if points:
                    # Calculate total sleep time
                    total_sleep_nanos = sum(
                        int(point['endTimeNanos']) - int(point['startTimeNanos'])
                        for point in points
                    )
                    sleep_hours = total_sleep_nanos / (3600 * 1e9)
                    
                    # Get bedtime and waketime
                    bedtime = datetime.fromtimestamp(int(points[0]['startTimeNanos']) / 1e9)
                    waketime = datetime.fromtimestamp(int(points[-1]['endTimeNanos']) / 1e9)
                    
                    # Determine sleep quality based on duration
                    if 7 <= sleep_hours <= 9:
                        quality = 'good'
                    elif 6 <= sleep_hours <= 10:
                        quality = 'fair'
                    else:
                        quality = 'poor'
                    
                    return {
                        'sleep_hours': round(sleep_hours, 1),
                        'sleep_quality': quality,
                        'bedtime': bedtime.strftime('%H:%M'),
                        'waketime': waketime.strftime('%H:%M')
                    }
        else:
            # Process session data
            session = sessions[0]
            start_nanos = int(session['startTimeMillis']) * 1e6
            end_nanos = int(session['endTimeMillis']) * 1e6
            
            sleep_duration_nanos = end_nanos - start_nanos
            sleep_hours = sleep_duration_nanos / (3600 * 1e9)
            
            bedtime = datetime.fromtimestamp(start_nanos / 1e9)
            waketime = datetime.fromtimestamp(end_nanos / 1e9)
            
            # Determine quality
            if 7 <= sleep_hours <= 9:
                quality = 'good'
            elif 6 <= sleep_hours <= 10:
                quality = 'fair'
            else:
                quality = 'poor'
            
            return {
                'sleep_hours': round(sleep_hours, 1),
                'sleep_quality': quality,
                'bedtime': bedtime.strftime('%H:%M'),
                'waketime': waketime.strftime('%H:%M')
            }
        
        return None
        
    except Exception as e:
        print(f"Error fetching sleep data: {e}")
        return None


def get_step_count(user, date=None):
    """
    Get step count from Google Fit for a specific date
    
    Args:
        user: Django user object
        date: datetime object (defaults to today)
    
    Returns:
        int: Total steps for the day
    """
    credentials = get_google_credentials(user)
    if not credentials:
        return None
    
    try:
        service = build('fitness', 'v1', credentials=credentials)
        
        if date is None:
            date = datetime.now()
        
        # Set time range for the day (midnight to midnight)
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        start_nanos = int(start_time.timestamp() * 1e9)
        end_nanos = int(end_time.timestamp() * 1e9)
        
        # Request step count data
        dataset_id = f"{start_nanos}-{end_nanos}"
        
        # Get step count from aggregated data
        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            }],
            "bucketByTime": {"durationMillis": 86400000},  # 1 day
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }
        
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        
        buckets = response.get('bucket', [])
        if buckets and buckets[0].get('dataset'):
            dataset = buckets[0]['dataset'][0]
            points = dataset.get('point', [])
            
            if points:
                total_steps = sum(
                    point['value'][0].get('intVal', 0)
                    for point in points
                )
                return total_steps
        
        return 0
        
    except Exception as e:
        print(f"Error fetching step count: {e}")
        return None


def get_activity_minutes(user, date=None):
    """
    Get active minutes from Google Fit for a specific date
    
    Args:
        user: Django user object
        date: datetime object (defaults to today)
    
    Returns:
        int: Total active minutes for the day
    """
    credentials = get_google_credentials(user)
    if not credentials:
        return None
    
    try:
        service = build('fitness', 'v1', credentials=credentials)
        
        if date is None:
            date = datetime.now()
        
        # Set time range for the day
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        # Request activity data
        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.active_minutes"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }
        
        response = service.users().dataset().aggregate(
            userId='me',
            body=body
        ).execute()
        
        buckets = response.get('bucket', [])
        if buckets and buckets[0].get('dataset'):
            dataset = buckets[0]['dataset'][0]
            points = dataset.get('point', [])
            
            if points:
                total_minutes = sum(
                    point['value'][0].get('intVal', 0)
                    for point in points
                )
                return total_minutes
        
        return 0
        
    except Exception as e:
        print(f"Error fetching activity minutes: {e}")
        return None


def sync_fitness_data(user, date=None):
    """
    Sync all fitness data for a user
    
    Args:
        user: Django user object
        date: datetime object (defaults to today)
    
    Returns:
        dict: All fitness data
    """
    sleep_data = get_sleep_data(user, date)
    step_count = get_step_count(user, date)
    active_minutes = get_activity_minutes(user, date)
    
    return {
        'sleep_data': sleep_data,
        'step_count': step_count,
        'active_minutes': active_minutes,
        'date': (date or datetime.now()).strftime('%Y-%m-%d')
    }
