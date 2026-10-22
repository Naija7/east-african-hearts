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
        db.rollback()
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
            cursor.close()
            return False, None, "Invalid or expired token"

        if datetime.fromisoformat(result['expires_at'].isoformat()) < datetime.now():
            # Delete expired token
            cursor.execute("DELETE FROM email_verifications WHERE token = %s", (token,))
            db.commit()
            cursor.close()
            return False, None, "Token has expired"

        user_id = result['user_id']

        # Mark email as verified
        cursor.execute("UPDATE users SET email_verified = TRUE WHERE id = %s", (user_id,))
        # Delete used token
        cursor.execute("DELETE FROM email_verifications WHERE token = %s", (token,))
        db.commit()

        cursor.close()
        return True, user_id, None

    except Exception as e:
        print(f"Error verifying token: {e}")
        db.rollback()
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
        cursor.close()
        return create_verification_token(user_id, db)

    except Exception as e:
        print(f"Error resending token: {e}")
        db.rollback()
        cursor.close()
        return None


# ----------------------------------------------------
# PASSWORD RESET TOKEN MANAGEMENT
# ----------------------------------------------------
def create_password_reset_token(user_id, db):
    """
    Generate and store password reset token for user (valid for 1 hour).
    Deletes any existing tokens for that user.
    """
    token = generate_verification_token(32)
    expires_at = datetime.now() + timedelta(hours=1)

    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM password_resets WHERE user_id = %s", (user_id,))
        cursor.execute("""
            INSERT INTO password_resets (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """, (user_id, token, expires_at))
        db.commit()
        cursor.close()
        return token
    except Exception as e:
        print(f"Error creating password reset token: {e}")
        db.rollback()
        cursor.close()
        return None


def verify_password_reset_token(token, db):
    """
    Verify password reset token.
    Returns: (is_valid, user_id, error_message)
    """
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT user_id, expires_at FROM password_resets
            WHERE token = %s
        """, (token,))
        record = cursor.fetchone()

        if not record:
            cursor.close()
            return False, None, "Invalid or expired reset link"

        if record['expires_at'] < datetime.now():
            cursor.execute("DELETE FROM password_resets WHERE token = %s", (token,))
            db.commit()
            cursor.close()
            return False, None, "Reset link has expired"

        user_id = record['user_id']
        cursor.close()
        return True, user_id, None
    except Exception as e:
        print(f"Error checking password reset token: {e}")
        db.rollback()
        cursor.close()
        return False, None, str(e)


def complete_password_reset(user_id, new_password_hash, db):
    """
    Update password and invalidate all reset tokens for this user.
    """
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_password_hash, user_id))
        cursor.execute("DELETE FROM password_resets WHERE user_id = %s", (user_id,))
        db.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error completing password reset: {e}")
        db.rollback()
        cursor.close()
        return False


# ----------------------------------------------------
# PASSWORD RESET TOKEN MANAGEMENT
# ----------------------------------------------------
def create_password_reset_token(user_id, db):
    """
    Generate and store password reset token for user (valid for 1 hour).
    Deletes any existing tokens for that user.
    """
    token = generate_verification_token(32)
    expires_at = datetime.now() + timedelta(hours=1)

    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM password_resets WHERE user_id = %s", (user_id,))
        cursor.execute("""
            INSERT INTO password_resets (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """, (user_id, token, expires_at))
        db.commit()
        cursor.close()
        return token
    except Exception as e:
        print(f"Error creating password reset token: {e}")
        db.rollback()
        cursor.close()
        return None


def verify_password_reset_token(token, db):
    """
    Verify password reset token.
    Returns: (is_valid, user_id, error_message)
    """
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT user_id, expires_at FROM password_resets
            WHERE token = %s
        """, (token,))
        record = cursor.fetchone()

        if not record:
            cursor.close()
            return False, None, "Invalid or expired reset link"

        if record['expires_at'] < datetime.now():
            cursor.execute("DELETE FROM password_resets WHERE token = %s", (token,))
            db.commit()
            cursor.close()
            return False, None, "Reset link has expired"

        user_id = record['user_id']
        cursor.close()
        return True, user_id, None
    except Exception as e:
        print(f"Error checking password reset token: {e}")
        db.rollback()
        cursor.close()
        return False, None, str(e)


def complete_password_reset(user_id, new_password_hash, db):
    """
    Update password and invalidate all reset tokens for this user.
    """
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_password_hash, user_id))
        cursor.execute("DELETE FROM password_resets WHERE user_id = %s", (user_id,))
        db.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error completing password reset: {e}")
        db.rollback()
        cursor.close()
        return False

