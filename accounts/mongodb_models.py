"""
MongoDB models/schemas for storing user wellness data
"""
from django.conf import settings
from datetime import datetime


def get_wellness_collection():
    """Get the wellness data collection"""
    return settings.MONGO_DB['user_wellness_data']


def get_achievements_collection():
    """Get the achievements collection"""
    return settings.MONGO_DB['user_achievements']


def get_streaks_collection():
    """Get the daily streaks collection"""
    return settings.MONGO_DB['daily_streaks']


# Achievement definitions
ACHIEVEMENTS = {
    'early_bird': {
        'id': 'early_bird',
        'name': 'Early Bird',
        'description': 'Woke up before 8 AM for 5 consecutive days',
        'icon': '🌅',
        'criteria': 'wake_before_8am_5days'
    },
    'step_master': {
        'id': 'step_master',
        'name': 'Step Master',
        'description': 'Walked 10,000+ steps in a day',
        'icon': '👟',
        'criteria': 'steps_10000_1day'
    },
    'study_buddy': {
        'id': 'study_buddy',
        'name': 'Study Buddy',
        'description': 'Attended all classes for a week',
        'icon': '📚',
        'criteria': 'perfect_attendance_7days'
    },
    'zen_master': {
        'id': 'zen_master',
        'name': 'Zen Master',
        'description': 'Maintained balance score above 80 for 3 days',
        'icon': '🧘',
        'criteria': 'balance_80_3days'
    },
    'night_owl_recovery': {
        'id': 'night_owl_recovery',
        'name': 'Night Owl Recovery',
        'description': 'Sleep before 11 PM for 3 consecutive days',
        'icon': '🌙',
        'criteria': 'sleep_before_11pm_3days'
    },
    'fitness_streak': {
        'id': 'fitness_streak',
        'name': 'Fitness Streak',
        'description': '7-day streak of 5000+ steps',
        'icon': '🔥',
        'criteria': 'steps_5000_7days'
    },
    'perfect_week': {
        'id': 'perfect_week',
        'name': 'Perfect Week',
        'description': 'Balance score above 70 for 7 consecutive days',
        'icon': '⭐',
        'criteria': 'balance_70_7days'
    }
}


def save_wellness_data(user_id, data):
    """
    Save wellness data to MongoDB
    
    Args:
        user_id: User ID
        data: dict containing wellness data
    
    Returns:
        Inserted document ID
    """
    collection = get_wellness_collection()
    
    document = {
        'user_id': user_id,
        'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
        'sleep_hours': data.get('sleep_hours'),
        'sleep_quality': data.get('sleep_quality'),
        'bedtime': data.get('bedtime'),
        'waketime': data.get('waketime'),
        'step_count': data.get('step_count'),
        'active_minutes': data.get('active_minutes'),
        'classes_attended': data.get('classes_attended'),
        'classes_total': data.get('classes_total'),
        'balance_score': data.get('balance_score'),
        'mood': data.get('mood'),
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    # Update or insert
    result = collection.update_one(
        {'user_id': user_id, 'date': document['date']},
        {'$set': document},
        upsert=True
    )
    
    return result.upserted_id or result.modified_count


def get_wellness_data(user_id, date=None):
    """
    Get wellness data for a specific date
    
    Args:
        user_id: User ID
        date: Date string (YYYY-MM-DD) or None for today
    
    Returns:
        Wellness data document or None
    """
    collection = get_wellness_collection()
    
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    return collection.find_one({'user_id': user_id, 'date': date})


def get_wellness_history(user_id, days=7):
    """
    Get wellness data history
    
    Args:
        user_id: User ID
        days: Number of days to retrieve
    
    Returns:
        List of wellness data documents
    """
    collection = get_wellness_collection()
    
    return list(collection.find(
        {'user_id': user_id}
    ).sort('date', -1).limit(days))


def initialize_user_achievements(user_id):
    """Initialize achievements for a new user"""
    collection = get_achievements_collection()
    
    for achievement_id, achievement in ACHIEVEMENTS.items():
        collection.update_one(
            {'user_id': user_id, 'achievement_id': achievement_id},
            {'$setOnInsert': {
                'user_id': user_id,
                'achievement_id': achievement_id,
                'name': achievement['name'],
                'description': achievement['description'],
                'icon': achievement['icon'],
                'unlocked': False,
                'unlocked_date': None,
                'progress': 0,
                'created_at': datetime.now()
            }},
            upsert=True
        )


def get_user_achievements(user_id):
    """Get all achievements for a user"""
    collection = get_achievements_collection()
    return list(collection.find({'user_id': user_id}))


def unlock_achievement(user_id, achievement_id):
    """Unlock an achievement for a user"""
    collection = get_achievements_collection()
    
    collection.update_one(
        {'user_id': user_id, 'achievement_id': achievement_id},
        {'$set': {
            'unlocked': True,
            'unlocked_date': datetime.now(),
            'updated_at': datetime.now()
        }}
    )


def update_achievement_progress(user_id, achievement_id, progress):
    """Update achievement progress"""
    collection = get_achievements_collection()
    
    collection.update_one(
        {'user_id': user_id, 'achievement_id': achievement_id},
        {'$set': {
            'progress': progress,
            'updated_at': datetime.now()
        }}
    )


def get_user_streak(user_id):
    """Get user's current streak"""
    collection = get_streaks_collection()
    return collection.find_one({'user_id': user_id})


def update_user_streak(user_id, current_streak, longest_streak=None):
    """Update user's streak"""
    collection = get_streaks_collection()
    
    update_data = {
        'user_id': user_id,
        'current_streak': current_streak,
        'last_sync_date': datetime.now().strftime('%Y-%m-%d'),
        'updated_at': datetime.now()
    }
    
    if longest_streak is not None:
        update_data['longest_streak'] = longest_streak
    
    collection.update_one(
        {'user_id': user_id},
        {'$set': update_data},
        upsert=True
    )
