"""Rate limiting for East African Hearts - prevents brute force and abuse"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from datetime import datetime, timedelta
import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use in-memory for now, can switch to Redis
)

# Custom rate limit decorators

def rate_limit_login(f):
    """5 login attempts per 15 minutes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return limiter.limit("5 per 15 minutes")(f)(*args, **kwargs)
    return decorated_function


def rate_limit_register(f):
    """1 registration per hour per IP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return limiter.limit("1 per hour")(f)(*args, **kwargs)
    return decorated_function


def rate_limit_like(f):
    """30 likes per minute"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return limiter.limit("30 per minute")(f)(*args, **kwargs)
    return decorated_function


def rate_limit_message(f):
    """10 messages per minute"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return limiter.limit("10 per minute")(f)(*args, **kwargs)
    return decorated_function


def rate_limit_testimonial(f):
    """1 testimonial per day"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return limiter.limit("1 per day")(f)(*args, **kwargs)
    return decorated_function


def rate_limit_api(f):
    """50 API requests per minute"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return limiter.limit("50 per minute")(f)(*args, **kwargs)
    return decorated_function


# Rate limit configuration summary
RATE_LIMITS = {
    'login': {
        'limit': '5 per 15 minutes',
        'description': 'Prevent brute force attacks',
        'message': 'Too many login attempts. Try again in 15 minutes.'
    },
    'register': {
        'limit': '1 per hour',
        'description': 'Prevent spam registrations',
        'message': 'Only one registration per hour per IP address.'
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
