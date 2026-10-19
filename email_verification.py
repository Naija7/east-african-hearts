"""Email verification and token management"""

import secrets
from datetime import datetime, timedelta
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


def generate_verification_token(length=32):
    """
    Generate a secure random verification token
    """
    return secrets.token_urlsafe(length)


def create_verification_token(user_id, db):
    """
    Create and store verification token for user
    Returns: token
    """
    token = generate_verification_token()
    expires_at = datetime.now() + timedelta(hours=24)  # Valid for 24 hours

    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO email_verifications (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """, (user_id, token, expires_at))
        db.commit()
        cursor.close()
        return token
    except Exception as e:
        print(f"Error creating verification token: {e}")
        cursor.close()
        return None


def verify_token(token, db):
    """
    Verify token and mark email as verified
    Returns: (success, user_id, error_message)
    """
    cursor = db.cursor(dictionary=True)

    try:
        # Check if token exists and is not expired
        cursor.execute("""
            SELECT user_id, expires_at FROM email_verifications
            WHERE token = %s
        """, (token,))

        result = cursor.fetchone()

        if not result:
            return False, None, "Invalid or expired token"

        if datetime.fromisoformat(result['expires_at'].isoformat()) < datetime.now():
            # Delete expired token
            cursor.execute("DELETE FROM email_verifications WHERE token = %s", (token,))
            db.commit()
            return False, None, "Token has expired"

        user_id = result['user_id']

        # Mark email as verified
        cursor.execute("UPDATE users SET email_verified = TRUE WHERE id = %s", (user_id,))
        db.commit()

        # Delete used token
        cursor.execute("DELETE FROM email_verifications WHERE token = %s", (token,))
        db.commit()

        cursor.close()
        return True, user_id, None

    except Exception as e:
        print(f"Error verifying token: {e}")
        cursor.close()
        return False, None, str(e)


def get_verification_status(user_id, db):
    """Check if user's email is verified"""
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT email_verified FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        return result['email_verified']
    return False


def resend_verification_token(user_id, db):
    """
    Resend verification token (delete old, create new)
    Returns: token
    """
    cursor = db.cursor()

    try:
        # Delete old token
        cursor.execute("DELETE FROM email_verifications WHERE user_id = %s", (user_id,))
        db.commit()

        # Create new token
        cursor.close()
        return create_verification_token(user_id, db)

    except Exception as e:
        print(f"Error resending token: {e}")
        cursor.close()
        return None
