"""Input validation and sanitization for East African Hearts"""

import re
from datetime import datetime

class ValidationError(Exception):
    """Custom validation exception"""
    pass


def validate_email(email):
    """
    Validate email format
    Returns: (is_valid, error_message)
    """
    if not email or len(email) > 254:
        return False, "Email is required and must be under 254 characters"

    # RFC 5322 simplified regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, None


def validate_password(password):
    """
    Validate password strength
    Requirements: min 8 chars, 1 uppercase, 1 number, 1 special char
    Returns: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)"

    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"

    return True, None


def validate_name(name):
    """
    Validate user name
    Requirements: 2-50 chars, letters and spaces only
    Returns: (is_valid, error_message)
    """
    if not name:
        return False, "Name is required"

    name = name.strip()

    if len(name) < 2:
        return False, "Name must be at least 2 characters"

    if len(name) > 100:
        return False, "Name must be under 100 characters"

    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']{2,100}$", name):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes"

    return True, None


def validate_age(age):
    """
    Validate age
    Requirements: 18-120 years
    Returns: (is_valid, error_message)
    """
    if not age:
        return False, "Age is required"

    try:
        age_int = int(age)
    except ValueError:
        return False, "Age must be a number"

    if age_int < 18:
        return False, "You must be at least 18 years old"

    if age_int > 120:
        return False, "Invalid age"

    return True, None


def validate_location(location):
    """
    Validate location
    Requirements: 2-100 chars
    Returns: (is_valid, error_message)
    """
    if not location:
        return False, "Location is required"

    location = location.strip()

    if len(location) < 2:
        return False, "Location must be at least 2 characters"

    if len(location) > 100:
        return False, "Location must be under 100 characters"

    # Alphanumeric, spaces, commas allowed
    if not re.match(r"^[a-zA-Z0-9\s,\-']{2,100}$", location):
        return False, "Location contains invalid characters"

    return True, None


def validate_bio(bio):
    """
    Validate user bio
    Requirements: max 500 chars, no HTML/scripts
    Returns: (is_valid, error_message)
    """
    if not bio:
        return True, None  # Bio is optional

    bio = bio.strip()

    if len(bio) > 500:
        return False, "Bio must be under 500 characters"

    # Check for HTML/script tags
    if re.search(r'<[^>]*>', bio):
        return False, "Bio cannot contain HTML tags"

    return True, None


def validate_interests(interests):
    """
    Validate interests
    Requirements: max 200 chars, comma-separated
    Returns: (is_valid, error_message)
    """
    if not interests:
        return True, None  # Interests are optional

    interests = interests.strip()

    if len(interests) > 200:
        return False, "Interests must be under 200 characters"

    # Check for HTML/script tags
    if re.search(r'<[^>]*>', interests):
        return False, "Interests cannot contain HTML tags"

    return True, None


def validate_message(message):
    """
    Validate message text
    Requirements: 1-1000 chars, no scripts
    Returns: (is_valid, error_message)
    """
    if not message or not message.strip():
        return False, "Message cannot be empty"

    message = message.strip()

    if len(message) > 1000:
        return False, "Message must be under 1000 characters"

    # Check for HTML/script tags
    if re.search(r'<[^>]*>', message):
        return False, "Message cannot contain HTML tags"

    return True, None


def validate_testimonial(male_name, female_name, country, story):
    """
    Validate testimonial submission
    Returns: (is_valid, error_message)
    """
    # Validate names
    is_valid, error = validate_name(male_name)
    if not is_valid:
        return False, f"Partner 1 Name: {error}"

    is_valid, error = validate_name(female_name)
    if not is_valid:
        return False, f"Partner 2 Name: {error}"

    # Validate country
    if not country or country == "":
        return False, "Country is required"

    if len(country) > 100:
        return False, "Country name is too long"

    # Validate story
    if not story or not story.strip():
        return False, "Love story is required"

    if len(story) < 10:
        return False, "Love story must be at least 10 characters"

    if len(story) > 5000:
        return False, "Love story must be under 5000 characters"

    # Check for HTML/scripts
    if re.search(r'<[^>]*>', story):
        return False, "Story cannot contain HTML tags"

    return True, None


def sanitize_input(text, max_length=1000):
    """
    Sanitize user input - remove special characters, limit length
    """
    if not text:
        return ""

    # Strip whitespace
    text = text.strip()

    # Limit length
    text = text[:max_length]

    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)

    return text
