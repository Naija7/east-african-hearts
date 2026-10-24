"""Rate limiting for East African Hearts - prevents brute force and abuse"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize rate limiter - storage backend configured in app.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Rate limit configuration summary
RATE_LIMITS = {
    'login': {
        'limit': '10 per 15 minutes',
        'description': 'Prevent brute force attacks',
        'message': 'Too many login attempts. Try again in 15 minutes.'
    },
    'register': {
        'limit': '10 per hour',
        'description': 'Prevent spam registrations',
        'message': 'Only 10 registrations per hour per IP address.'
    },
    'like': {
        'limit': '30 per minute',
        'description': 'Prevent bot-like activity',
        'message': 'You are liking profiles too fast. Please slow down.'
    },
    'message': {
        'limit': '10 per minute',
        'description': 'Prevent message spam',
        'message': 'You are sending messages too fast. Please slow down.'
    },
    'testimonial': {
        'limit': '1 per day',
        'description': 'Prevent spam testimonials',
        'message': 'You can only submit one testimonial per day.'
    },
    'api': {
        'limit': '50 per minute',
        'description': 'General API rate limit',
        'message': 'API rate limit exceeded. Try again later.'
    }
}

print("Rate Limiting Configuration:")
for action, config in RATE_LIMITS.items():
    print(f"  {action.upper()}: {config['limit']} - {config['description']}")
