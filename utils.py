"""Image optimization utilities for East African Hearts"""

from PIL import Image
import io
import os
import traceback
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Logging functions for structured error handling
def log_error(msg, exc_info=None, user_id=None):
    """Log an error with optional exception info"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg = f"[{timestamp}] ERROR: {msg}"
    if exc_info:
        error_msg += f"\n{traceback.format_exc()}"
    print(error_msg)

    # Also log to database if user_id provided
    if user_id:
        log_event(user_id, 'ERROR', msg, level='ERROR')


def log_warning(msg, user_id=None):
    """Log a warning message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] WARNING: {msg}")
    if user_id:
        log_event(user_id, 'WARNING', msg, level='WARNING')


def log_info(msg, user_id=None):
    """Log an info message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] INFO: {msg}")
    if user_id:
        log_event(user_id, 'INFO', msg, level='INFO')


def compress_image(image_file, max_width=600, max_height=600, quality=80):
    """
    Compress and resize image for optimal storage and performance

    Args:
        image_file: File object from form upload
        max_width: Maximum width in pixels (default 600)
        max_height: Maximum height in pixels (default 600)
        quality: JPEG quality 1-100 (default 80)

    Returns:
        Compressed image bytes, or None if error
    """
    try:
        # Open image
        img = Image.open(image_file)

        # Convert RGBA to RGB (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img

        # Resize if needed (maintain aspect ratio)
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Save to bytes with compression
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
        img_byte_arr.seek(0)

        # Check size (max 2MB)
        size_mb = len(img_byte_arr.getvalue()) / (1024 * 1024)
        if size_mb > 2:
            # Further compress if over 2MB
            return compress_image(image_file, max_width=500, max_height=500, quality=70)

        return img_byte_arr.getvalue()

    except Exception as e:
        log_error(f"Image compression error: {e}", exc_info=True)
        return None


def get_image_size_mb(image_bytes):
    """Get image size in MB"""
    return len(image_bytes) / (1024 * 1024)


def validate_image_file(file_obj, max_size_mb=5):
    """
    Validate image file before processing

    Args:
        file_obj: File object
        max_size_mb: Maximum file size in MB

    Returns:
        (is_valid, error_message)
    """
    if not file_obj:
        return True, None  # No file is ok (optional)

    # Check file extension
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    filename = file_obj.filename.lower()

    if not any(filename.endswith('.' + ext) for ext in ALLOWED_EXTENSIONS):
        return False, "Invalid file type. Allowed: JPG, PNG, GIF, WebP"

    # Check file size
    file_obj.seek(0, os.SEEK_END)
    file_size_mb = file_obj.tell() / (1024 * 1024)
    file_obj.seek(0)

    if file_size_mb > max_size_mb:
        return False, f"File too large. Max {max_size_mb}MB. Your file: {file_size_mb:.1f}MB"

    return True, None


def log_event(user_id, event_type, details="", level="INFO"):
    """Log an event to the database"""
    try:
        from db import get_db_connection
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO logs (user_id, event_type, details, created_at)
            VALUES (%s, %s, %s, %s)
        """, (user_id, event_type, details, datetime.now()))
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        log_error(f"Failed to log event: {event_type}", exc_info=True)
