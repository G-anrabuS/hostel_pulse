"""
Data synchronization service for collecting and storing wellness data
"""
from datetime import datetime, timedelta
from .google_fit_service import sync_fitness_data
from .google_calendar_service import calculate_attendance
from .mongodb_models import (
    save_wellness_data, get_wellness_data, get_wellness_history,
    initialize_user_achievements, get_user_achievements, unlock_achievement,
    update_achievement_progress, get_user_streak, update_user_streak
)


def calculate_balance_score(wellness_data):
    """
    Calculate balance score from wellness data
    
    Args:
        wellness_data: dict containing wellness metrics
    
    Returns:
        int: Balance score (0-100)
    """
    score = 50  # Base score
    
    # Sleep (30 points)
    sleep_hours = wellness_data.get('sleep_hours', 0)
    if sleep_hours:
        if 7 <= sleep_hours <= 9:
            score += 30
        elif 6 <= sleep_hours <= 10:
            score += 15
        else:
            score -= 10
    
    # Activity (25 points)
    step_count = wellness_data.get('step_count', 0)
    if step_count >= 10000:
        score += 25
    elif step_count >= 5000:
        score += 15
    elif step_count >= 2000:
        score += 5
    
    # Classes (25 points)
    classes_total = wellness_data.get('classes_total', 0)
    classes_attended = wellness_data.get('classes_attended', 0)
    if classes_total > 0:
        attendance_rate = classes_attended / classes_total
        if attendance_rate >= 0.9:
            score += 25
        elif attendance_rate >= 0.7:
            score += 15
        elif attendance_rate >= 0.5:
            score += 5
    
    # Active minutes (20 points)
    active_minutes = wellness_data.get('active_minutes', 0)
    if active_minutes >= 30:
        score += 20
    elif active_minutes >= 15:
        score += 10
    
    return min(100, max(0, score))


def sync_user_data(user):
    """
    Main sync function to collect all user data
    
    Args:
        user: Django user object
    
    Returns:
        dict: Synced wellness data
    """
    try:
        # Collect fitness data from Google Fit
        fitness_data = sync_fitness_data(user)
        
        # Collect calendar data
        attendance_data = calculate_attendance(user)
        
        # Combine all data
        wellness_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'sleep_hours': fitness_data.get('sleep_data', {}).get('sleep_hours') if fitness_data.get('sleep_data') else None,
            'sleep_quality': fitness_data.get('sleep_data', {}).get('sleep_quality') if fitness_data.get('sleep_data') else None,
            'bedtime': fitness_data.get('sleep_data', {}).get('bedtime') if fitness_data.get('sleep_data') else None,
            'waketime': fitness_data.get('sleep_data', {}).get('waketime') if fitness_data.get('sleep_data') else None,
            'step_count': fitness_data.get('step_count', 0),
            'active_minutes': fitness_data.get('active_minutes', 0),
            'classes_attended': attendance_data.get('classes_attended', 0),
            'classes_total': attendance_data.get('classes_total', 0),
        }
        
        # Calculate balance score
        wellness_data['balance_score'] = calculate_balance_score(wellness_data)
        
        # Save to MongoDB
        save_wellness_data(user.id, wellness_data)
        
        # Update achievements
        update_achievements(user.id)
        
        # Update streak
        update_streak(user.id)
        
        return wellness_data
        
    except Exception as e:
        print(f"Error syncing user data: {e}")
        return None


def update_achievements(user_id):
    """
    Check and update user achievements
    
    Args:
        user_id: User ID
    """
    # Initialize achievements if not exists
    initialize_user_achievements(user_id)
    
    # Get recent wellness history
    history = get_wellness_history(user_id, days=7)
    
    if not history:
        return
    
    # Check each achievement
    check_early_bird(user_id, history)
    check_step_master(user_id, history)
    check_study_buddy(user_id, history)
    check_zen_master(user_id, history)
    check_night_owl_recovery(user_id, history)
    check_fitness_streak(user_id, history)
    check_perfect_week(user_id, history)


def check_early_bird(user_id, history):
    """Check Early Bird achievement"""
    consecutive_days = 0
    for day in history:
        waketime = day.get('waketime')
        if waketime:
            hour = int(waketime.split(':')[0])
            if hour < 8:
                consecutive_days += 1
            else:
                break
    
    update_achievement_progress(user_id, 'early_bird', consecutive_days)
    if consecutive_days >= 5:
        unlock_achievement(user_id, 'early_bird')


def check_step_master(user_id, history):
    """Check Step Master achievement"""
    for day in history:
        if day.get('step_count', 0) >= 10000:
            unlock_achievement(user_id, 'step_master')
            break


def check_study_buddy(user_id, history):
    """Check Study Buddy achievement"""
    if len(history) < 7:
        return
    
    perfect_attendance = all(
        day.get('classes_attended', 0) == day.get('classes_total', 0) and day.get('classes_total', 0) > 0
        for day in history[:7]
    )
    
    if perfect_attendance:
        unlock_achievement(user_id, 'study_buddy')


def check_zen_master(user_id, history):
    """Check Zen Master achievement"""
    consecutive_days = 0
    for day in history:
        if day.get('balance_score', 0) >= 80:
            consecutive_days += 1
        else:
            break
    
    update_achievement_progress(user_id, 'zen_master', consecutive_days)
    if consecutive_days >= 3:
        unlock_achievement(user_id, 'zen_master')


def check_night_owl_recovery(user_id, history):
    """Check Night Owl Recovery achievement"""
    consecutive_days = 0
    for day in history:
        bedtime = day.get('bedtime')
        if bedtime:
            hour = int(bedtime.split(':')[0])
            if hour < 23:
                consecutive_days += 1
            else:
                break
    
    update_achievement_progress(user_id, 'night_owl_recovery', consecutive_days)
    if consecutive_days >= 3:
        unlock_achievement(user_id, 'night_owl_recovery')


def check_fitness_streak(user_id, history):
    """Check Fitness Streak achievement"""
    if len(history) < 7:
        return
    
    streak = all(day.get('step_count', 0) >= 5000 for day in history[:7])
    
    if streak:
        unlock_achievement(user_id, 'fitness_streak')


def check_perfect_week(user_id, history):
    """Check Perfect Week achievement"""
    if len(history) < 7:
        return
    
    perfect_week = all(day.get('balance_score', 0) >= 70 for day in history[:7])
    
    if perfect_week:
        unlock_achievement(user_id, 'perfect_week')


def update_streak(user_id):
    """
    Update user's daily streak
    
    Args:
        user_id: User ID
    """
    streak_data = get_user_streak(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not streak_data:
        # First time
        update_user_streak(user_id, 1, 1)
        return
    
    last_sync = streak_data.get('last_sync_date')
    current_streak = streak_data.get('current_streak', 0)
    longest_streak = streak_data.get('longest_streak', 0)
    
    if last_sync == today:
        # Already synced today
        return
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    if last_sync == yesterday:
        # Continuing streak
        current_streak += 1
    else:
        # Streak broken
        current_streak = 1
    
    # Update longest streak
    if current_streak > longest_streak:
        longest_streak = current_streak
    
    update_user_streak(user_id, current_streak, longest_streak)


def get_user_dashboard_data(user):
    """
    Get all data needed for dashboard
    
    Args:
        user: Django user object
    
    Returns:
        dict: Dashboard data
    """
    # Get today's data
    today_data = get_wellness_data(user.id)
    
    # Get history
    history = get_wellness_history(user.id, days=7)
    
    # Get achievements
    achievements = get_user_achievements(user.id)
    
    # Get streak
    streak = get_user_streak(user.id)
    
    return {
        'today': today_data,
        'history': history,
        'achievements': achievements,
        'streak': streak
    }
