"""
Gemini API Service for generating personalized wellness suggestions
"""
import os
from django.conf import settings

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("WARNING: google-genai not installed. Install with: pip install google-genai")


# Fallback suggestions for when Gemini API is unavailable
FALLBACK_SUGGESTIONS = {
    'tired': [
        'Take a short 20-minute power nap?',
        'Drink some water and step outside for fresh air?',
        'Try some light stretching to boost energy?'
    ],
    'stressed': [
        'Try deep breathing for 5 minutes?',
        'Listen to calming music or nature sounds?',
        'Talk to a friend or write down your thoughts?'
    ],
    'active': [
        'Keep up the energy! Plan your next goal?',
        'Share your motivation with study group?',
        'Channel that energy into a productive task?'
    ],
    'balanced': [
        'Take a 10-minute walk around campus?',
        'Join a library study group?',
        'Take a well-deserved break, you earned it!'
    ]
}


def initialize_gemini():
    """Initialize Gemini API with API key from settings"""
    if not GEMINI_AVAILABLE:
        return False
    
    if not settings.GEMINI_API_KEY:
        return False
    
    try:
        # Configure the client with API key
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return client
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
        return False


def generate_wellness_suggestions(mood, balance_score, user_name="Student", wellness_context=None):
    """
    Generate personalized wellness suggestions using Gemini API
    
    Args:
        mood (str): Current mood (tired, stressed, active, balanced)
        balance_score (int): Current balance score (0-100)
        user_name (str): User's name for personalization
        wellness_context (dict): Real wellness data (sleep, steps, classes, etc.)
    
    Returns:
        list: List of 3 wellness suggestions
    """
    # Try Gemini API first
    client = initialize_gemini()
    if client and wellness_context:
        try:
            suggestions = _generate_with_gemini(client, mood, balance_score, user_name, wellness_context)
            if suggestions:
                return suggestions
        except Exception as e:
            print(f"Gemini API error: {e}")
    
    # Fallback to static suggestions
    return FALLBACK_SUGGESTIONS.get(mood, FALLBACK_SUGGESTIONS['balanced'])


def _generate_with_gemini(client, mood, balance_score, user_name, wellness_context):
    """Internal function to call Gemini API"""
    try:
        # Extract wellness data
        sleep_hours = wellness_context.get('sleep_hours')
        sleep_quality = wellness_context.get('sleep_quality')
        step_count = wellness_context.get('step_count', 0)
        active_minutes = wellness_context.get('active_minutes', 0)
        classes_attended = wellness_context.get('classes_attended', 0)
        classes_total = wellness_context.get('classes_total', 0)
        
        # Build detailed wellness summary
        wellness_summary = []
        if sleep_hours:
            wellness_summary.append(f"Slept {sleep_hours} hours ({sleep_quality} quality)")
        if step_count:
            wellness_summary.append(f"Walked {step_count:,} steps today")
        if active_minutes:
            wellness_summary.append(f"{active_minutes} active minutes")
        if classes_total:
            attendance_rate = (classes_attended / classes_total * 100) if classes_total > 0 else 0
            wellness_summary.append(f"Attended {classes_attended}/{classes_total} classes ({attendance_rate:.0f}%)")
        
        wellness_text = "\n- ".join(wellness_summary) if wellness_summary else "No data synced yet"
        
        # Craft a highly personalized prompt
        prompt = f"""You are a friendly, supportive wellness advisor for {user_name}, a college student living in a hostel.

CURRENT SITUATION:
- Mood: {mood}
- Overall Wellness Score: {balance_score}/100
- Today's Data:
  - {wellness_text}

CONTEXT & INSIGHTS:
"""
        
        # Add specific insights based on data
        if sleep_hours:
            if sleep_hours < 6:
                prompt += f"- {user_name} is sleep-deprived (only {sleep_hours}h). This affects focus and energy.\n"
            elif sleep_hours > 9:
                prompt += f"- {user_name} slept {sleep_hours}h (oversleeping). May indicate stress or avoidance.\n"
            else:
                prompt += f"- Sleep is decent ({sleep_hours}h), but quality is {sleep_quality}.\n"
        
        if step_count:
            if step_count < 2000:
                prompt += f"- Very sedentary today ({step_count} steps). Needs movement.\n"
            elif step_count < 5000:
                prompt += f"- Below average activity ({step_count} steps). Could use more movement.\n"
            elif step_count >= 10000:
                prompt += f"- Great activity level ({step_count} steps)! Keep it up.\n"
        
        if classes_total:
            attendance_rate = (classes_attended / classes_total * 100) if classes_total > 0 else 0
            if attendance_rate < 70:
                prompt += f"- Missing classes ({attendance_rate:.0f}% attendance). Academic concern.\n"
            elif attendance_rate == 100:
                prompt += f"- Perfect attendance today! Academically engaged.\n"
        
        prompt += f"""
TASK: Generate exactly 3 SHORT, SPECIFIC, ACTIONABLE suggestions for {user_name} RIGHT NOW.

CRITICAL REQUIREMENTS:
1. Use {user_name}'s actual data above - be SPECIFIC (mention actual numbers when relevant)
2. Address their CURRENT mood ({mood}) and wellness score ({balance_score})
3. Each suggestion must be under 12 words
4. Make them feel personal, not generic
5. Focus on IMMEDIATE actions they can take in the next 30 minutes
6. End each with "?" to feel optional and friendly
7. Be encouraging but realistic - no toxic positivity

EXAMPLES OF GOOD SUGGESTIONS:
- "You've only walked {step_count} steps - take a 10-minute walk?"
- "Slept {sleep_hours}h - grab a power nap before studying?"
- "Missed some classes - message a classmate for notes?"

FORMAT: Return ONLY 3 suggestions, one per line, nothing else."""

        # Generate content using the new API
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        if response and response.text:
            # Parse the response into a list
            suggestions = [s.strip() for s in response.text.strip().split('\n') if s.strip()]
            
            # Ensure we have exactly 3 suggestions
            if len(suggestions) >= 3:
                return suggestions[:3]
            elif len(suggestions) > 0:
                # If we got fewer than 3, pad with fallback
                fallback = FALLBACK_SUGGESTIONS.get(mood, FALLBACK_SUGGESTIONS['balanced'])
                while len(suggestions) < 3:
                    suggestions.append(fallback[len(suggestions) % len(fallback)])
                return suggestions[:3]
        
        return None
        
    except Exception as e:
        print(f"Error generating with Gemini: {e}")
        return None


def get_mood_message(mood):
    """Get appropriate message for the mood"""
    messages = {
        'tired': "You're feeling tired. Rest is important.",
        'stressed': "You're feeling stressed. Take it one step at a time.",
        'active': "You're feeling active! Channel that energy positively.",
        'balanced': "You're in a good balance. Keep it up!"
    }
    return messages.get(mood, messages['balanced'])
